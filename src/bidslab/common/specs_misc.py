#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Iterable,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from warnings import warn

import pandas as pd

from bidslab._typing import A
from bidslab.common.base import BaseAcquisition, Entity
from bidslab.settings import get_settings_value
from bidslab.utils.checks import check_if_valid_uri
from bidslab.utils.dict_manipulation import clean_dict, manipulate_dictkeys
from bidslab.utils.exceptions import (
    FieldEntryNotValidError,
    TopLevelEntityNotLinkedWarning,
)
from bidslab.utils.helpers import (
    add_object_to_sequence,
    append_path,
    check_entity_mismatch,
    copy_file,
    get_entity_from_file,
    load_tsv_data,
    parse_descriptive_tsv,
    parse_json_sidecar,
    set_attr_from_dict,
    write_entities,
    write_json,
)
from bidslab.utils.string_manipulation import to_snakecase

if TYPE_CHECKING:
    from bidslab.common.specs_task import Task

FORMAT_ALLOWED_FIELD_ENTRIES = {
    "string",
    "number",
    "integer",
    "boolean",
    "index",
    "label",
    "date",
    "datetime",
    "time",
    "unit",
    "uri",
    "rrid",
    "bids_uri",
    "dataset_relative",
    "file_relative",
    "participant_relative",
    "stimuli_relative",
    "hed_version",
}


@dataclass(slots=True)
class Filter:
    name: str
    parameters: MutableMapping[str, str]


@dataclass(slots=True)
class Level:
    level_name: str
    description: str
    term_url: str | None = None

    def __post_init__(self) -> None:
        if self.term_url:
            check_if_valid_uri(self.term_url)

    def __repr__(self) -> str:
        return f"<Level name={self.level_name}>"


@dataclass(slots=True)
class Hardware:
    manufacturer: str | None = None
    manufacturers_model_name: str | None = None
    software_versions: str | None = None
    device_serial_number: str | None = None

    def __repr__(self) -> str:
        return (
            f"<Hardware manufacturer={self.manufacturer} "
            f"model={self.manufacturers_model_name}>"
        )


@dataclass(slots=True)
class Institution:
    institution_name: str | None = None
    institution_address: str | None = None
    institutional_department_name: str | None = None

    def __repr__(self) -> str:
        return f"<Institution name={self.institution_name}>"


class Column:
    def __init__(
        self, name: str, **kwargs: str | int | float | Mapping | Iterable
    ) -> None:
        self.column_name: str = name

        self.long_name: str | None = None
        self.description: str | None = None
        self._format: str | None = None
        self.units: str | None = None
        self.delimiter: str | None = None
        self.term_url: str | None = None
        self.hed: str | Mapping[str, str] | None = None
        self.maximum: int | float | None = None
        self.minimum: int | float | None = None

        if get_settings_value("SUPPORT_OLD_VERSIONS"):
            self.unit: str | None = None

        self._levels: Iterable[Level] | None = None

        set_attr_from_dict(self, kwargs)

        if self.term_url and not get_settings_value("OVERRIDE_VALIDATION"):
            check_if_valid_uri(self.term_url)

    def __repr__(self) -> str:
        return f"<Column name={self.column_name} format={self.format}>"

    @property
    def format(self) -> str | None:
        return self._format

    @format.setter  # noqa: A003
    def format(self, value: str) -> None:
        if value not in FORMAT_ALLOWED_FIELD_ENTRIES:
            raise FieldEntryNotValidError(
                f"Field `Format` must be one of {FORMAT_ALLOWED_FIELD_ENTRIES}"
            )
        self._format = value

    @property
    def levels(self) -> Iterable[Level] | None:
        return self._levels

    @levels.setter
    def levels(self, value: Mapping | Iterable[Level]) -> None:
        if isinstance(value, Mapping):
            self._levels = []
            for key, val in value.items():
                if isinstance(val, Mapping):
                    val = {
                        to_snakecase(level_key): level_val
                        for level_key, level_val in val.items()
                    }
                    level = Level(level_name=key, **val)
                else:
                    level = Level(level_name=key, description=val)

                self._levels.append(level)
        elif isinstance(value, Iterable) and all(isinstance(v, Level) for v in value):
            self._levels = value
        else:
            raise TypeError("Field `Levels` must be a list of Level objects")


@dataclass
class Event:
    def __init__(
        self,
        onset: float,
        duration: float,
        **kwargs: Any,
    ) -> None:
        self.onset: float = onset

        self.duration: float = duration

        self.columns: dict[str, Any] | None = None

        for key, value in kwargs.items():
            setattr(self, key, value)


class Recording(Entity):
    def __init__(
        self,
        base_path: os.PathLike | str,
        recording_id: str,
        sampling_frequency: int | float,
        virtual_entity: bool = False,
    ):
        super().__init__(
            _entity_id=recording_id,
            _entity_name="recording",
            _virtual_entity=virtual_entity,
        )
        self.recording_id: str = self._entity_id
        self.sampling_frequency: int | float = sampling_frequency

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._run: Run | None = None

        self._data: Any | None = None

    @property
    def run(self) -> "Run | None":
        if self._run:
            return self._run

        warn("Recording is not linked to a Run object.", TopLevelEntityNotLinkedWarning)
        return self._run

    @run.setter
    def run(self, value: "Run") -> None:
        self._run = value

    def get_top_level_entities(self) -> list[str | Any]:
        assert self.run is not None
        entities = self.run.get_top_level_entities()
        entities.append(self.recording_id)
        return entities

    # def write(self, output_path: os.PathLike | str) -> None:
    #    # TODO: implement writing of basic Recording data
    #    if not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
    #        raise NotImplementedError


class PhysioRecording(Recording):
    def __init__(
        self,
        base_path: os.PathLike | str,
        recording_id: str,
        sampling_frequency: int,
        start_time: int | float,
        columns: MutableSequence[Column],
        hardware: Hardware | None = None,
        virtual_entity: bool = False,
        **kwargs: Any,
    ):
        super().__init__(
            base_path=base_path,
            recording_id=recording_id,
            sampling_frequency=sampling_frequency,
            virtual_entity=virtual_entity,
        )

        self.start_time: int | float = start_time
        self.columns: MutableSequence[Column] = columns
        self.hardware: Hardware | None = hardware

        self._data: Any | None = None
        self._events: Sequence[Event] | None = None

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def events(self) -> Sequence[Event] | None:
        if not self._events:
            self._events = get_events_from_files(
                self, self.root, file_ending="physioevents"
            )

        return self._events

    @events.setter
    def events(self, value: Sequence[Event]) -> None:
        self._events = value

    def write(self, output_path: os.PathLike | str) -> None:
        output_path_json = append_path(output_path, "_physio.json")
        output_path_tsv = append_path(output_path, "_physio.tsv.gz")

        # write data into _physio.tsv.gz
        data_tsv = self._data
        if data_tsv is None:  # TODO remove
            data_tsv = pd.DataFrame()
        data_tsv.to_csv(
            output_path_tsv,
            sep="\t",
            index=False,
            header=False,
            compression="gzip",
        )

        # write json sidecar
        description = self.__dict__.copy()
        description.pop("_data", None)
        description.pop("_events", None)
        description.pop("recording_id", None)
        description = clean_dict(description)
        write_json(description, output_path_json)

        # write physioevents
        if self.events:
            write_events_to_files(
                self,
                self.events,
                output_path,
                file_ending="physioevents",
                compressed=True,
            )


class StimRecording(Recording):
    def __init__(
        self,
        base_path: os.PathLike | str,
        recording_id: str,
        sampling_frequency: int,
        start_time: int | float,
        columns: MutableSequence[Column],
        virtual_entity: bool = False,
        **kwargs,
    ):
        super().__init__(
            base_path=base_path,
            recording_id=recording_id,
            sampling_frequency=sampling_frequency,
            virtual_entity=virtual_entity,
        )

        self.root: pathlib.Path = pathlib.Path(base_path)
        self.start_time: int | float = start_time
        self.columns: MutableSequence[Column] = columns

        self._data: Any | None = None

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def data(self) -> Any | None:
        return self._data

    @data.setter
    def data(self, value: pd.DataFrame) -> None:
        self._data = value

    def write(self, output_path: os.PathLike | str) -> None:
        output_path_json = append_path(output_path, "_stim.json")
        output_path_tsv = append_path(output_path, "_stim.tsv.gz")

        # write tsv.gz
        data_tsv = self.data
        if data_tsv is None:  # TODO remove
            data_tsv = pd.DataFrame()
        data_tsv.to_csv(
            output_path_tsv,
            sep="\t",
            index=False,
            header=False,
            compression="gzip",
        )

        # write json sidecar
        description = self.__dict__.copy()
        description.pop("data", None)
        description.pop("recording_id", None)
        description = clean_dict(description)
        write_json(description, output_path_json)


class Run(Entity, Generic[A]):
    def __init__(
        self,
        base_path: os.PathLike | str,
        run_id: int,
        virtual_entity: bool = False,
        **kwargs: Any,
    ):
        if not isinstance(run_id, int):
            raise TypeError("run_id must be an index of type integer")
        run_id_str = str(run_id)
        super().__init__(
            _entity_id="run-" + run_id_str,
            _entity_name="run",
            _virtual_entity=virtual_entity,
        )
        self.run_id: str = self._entity_id

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._acquisition: A | None = None

        self._physio: dict[str, PhysioRecording] | None = None
        self._stims: dict[str, StimRecording] | None = None

        set_attr_from_dict(self, kwargs)

    def __repr__(self):
        return f"Run id={self.run_id}"

    @property
    def acquisition(self) -> A | None:
        if self._acquisition:
            return self._acquisition

        warn(
            "Run is not linked to a Acquisition object.", TopLevelEntityNotLinkedWarning
        )
        return self._acquisition

    @acquisition.setter
    def acquisition(self, value: A) -> None:
        self._acquisition = value

    @property
    def physio(self) -> dict[str, PhysioRecording] | None:
        if self._physio is None:
            recording_labels = get_recordings_from_files(self, self.root, "physio")
            if not recording_labels:
                return None
            self._physio = {}
            files = self.root.glob("*_physio.json")

            for key, value in recording_labels.items():
                # get description (load json sidecar)
                entitylist = self.get_top_level_entities()
                entitylist.append(key)

                description = {}
                for file in files:
                    if check_entity_mismatch(
                        file.stem.removesuffix("_physio"),
                        entitylist,
                    ):
                        description = parse_json_sidecar(file)

                # create the entity with the loaded description
                if description:
                    # TODO create hardware and columns as class
                    description = manipulate_dictkeys(description, to_snakecase)
                    self._physio[key] = PhysioRecording(
                        recording_id=key,
                        virtual_entity=value,
                        base_path=self.root,
                        run=self,
                        **description,
                    )
                else:
                    raise FileNotFoundError

        return self._physio

    @physio.setter
    def physio(self, value: Sequence[dict] | Sequence[PhysioRecording]) -> None:
        self._physio = {}
        for entry in value:
            if isinstance(entry, dict):
                self._physio.update(entry)
            elif isinstance(entry, PhysioRecording):
                self._physio.update({entry.recording_id: entry})

    @property
    def stims(self) -> dict[str, StimRecording] | None:
        if self._stims is None:
            self._stims = get_stims_from_files(self, self.root)
        return self._stims

    @stims.setter
    def stims(self, value: dict[str, StimRecording]) -> None:
        self._stims = value

    def get_top_level_entities(self) -> list[str | Any]:
        assert self.acquisition is not None
        entities = self.acquisition.get_top_level_entities()
        entities.append(self.run_id)
        return entities

    def write(self, output_path: os.PathLike | str) -> None:
        if self.physio:
            write_entities(output_path, self.physio.values())
        if self.stims:
            write_entities(output_path, self.stims.values())


class Acquisition(BaseAcquisition):
    def __init__(
        self,
        base_path: os.PathLike | str,
        acquisition_id: str,
        virtual_entity: bool = False,
    ):
        super().__init__(
            base_path=base_path,
            acquisition_id=acquisition_id,
            virtual_entity=virtual_entity,
        )

        self._task: Task | None = None

    @property
    def runs(self) -> dict[str, Run]:
        if not self._runs:
            self._runs = {}
            files = self.root.iterdir()
            run_ids = set()
            for file in files:
                try:
                    run_ids.add(
                        get_entity_from_file(
                            file,
                            "run",
                        )["run"]
                    )
                except KeyError:
                    continue
            for run_id in run_ids:
                run_id_int = int(run_id.split("-")[1])
                self._runs.update(
                    {
                        f"run-{run_id_int}": Run(
                            run_id=run_id_int,
                            base_path=self.root,
                            acquisition=self,
                        )
                    }
                )
            # If no runs are found, add a default one
            if not self._runs:
                self._runs.update(
                    {
                        "run-0": Run(
                            run_id=0,
                            base_path=self.root,
                            acquisition=self,
                        )
                    }
                )

        return self._runs

    @runs.setter
    def runs(self, value: Sequence[int | Run] | dict[str, Run]) -> None:
        if isinstance(value, Sequence):
            if all(isinstance(entry, int) for entry in value):
                self._runs = {}
                for entry in value:
                    assert isinstance(entry, int)  # for mypy
                    self._runs.update(
                        {
                            f"run-{entry}": Run(
                                run_id=entry, base_path=self.root, acquisition=self
                            )
                        }
                    )
            elif all(isinstance(v, Run) for v in value):
                self._runs = {}
                for entry in value:
                    assert isinstance(entry, Run)  # for mypy
                    self._runs.update({entry.run_id: entry})
        elif isinstance(value, dict):
            self._runs = value
        raise TypeError("Field `Runs` must be a list or dict of Run objects")

    @property
    def task(self) -> "Task | None":
        if self._task:
            return self._task

        warn(
            "Acquisition is not linked to a Task object.",
            TopLevelEntityNotLinkedWarning,
        )
        return self._task

    @task.setter
    def task(self, value: "Task") -> None:
        self._task = value

    def get_top_level_entities(self) -> list[str | Any]:
        assert self.task is not None
        entities = self.task.get_top_level_entities()
        entities.append(self.acquisition_id)
        return entities


def get_recordings_from_files(
    run: Run, base_path: os.PathLike | str, file_ending: str
) -> dict[str, bool]:
    # file_ending eg "physio" or "eeg", not extension eg ".json"
    # returns all rercording-labels and if they are virtual entities
    labels = {}

    base_path = pathlib.Path(base_path)
    files = base_path.glob(f"*_{file_ending}.*")
    for file in files:
        try:
            label = get_entity_from_file(file, "recording")["recording"]
            entities = run.get_top_level_entities()
            entities.append(f"recording-{label}")
            if check_entity_mismatch(file.stem.removesuffix("_physio"), entities):
                labels[f"recording-{label}"] = False

        except KeyError:
            continue

    if not labels:
        files = base_path.glob(f"*_{file_ending}.*")
        for file in files:
            # check if a file matches
            if check_entity_mismatch(
                file.stem.removesuffix("_physio"), run.get_top_level_entities()
            ):
                labels["recording-00"] = True
                break

    return labels


def get_events_from_files(
    cls: Recording | Run, base_path: os.PathLike | str, file_ending="events"
) -> MutableSequence[Event] | None:
    base_path = pathlib.Path(base_path)

    events: MutableSequence[Event] = []
    columns: MutableMapping[Any, Any] = {}

    # get list of top level entities
    entities = cls.get_top_level_entities()

    # sequence of all possible folders
    # in the correct input order (deepest to dataset_root)
    folders_json = [base_path]
    path = base_path
    target = entities[0]
    while path.name != target:
        path = path.parent
        folders_json.append(path)
    path = path.parent
    folders_json.append(path)

    folders_tsv = [base_path, base_path.parent]

    for folder in folders_json:
        if columns == {}:
            # get all possible files with _events.json
            files_json = list(folder.glob(f"*_{file_ending}.json"))
            filenames_json = [f.name for f in files_json]
            file_entities_json = [
                f.removesuffix(f"_{file_ending}.json") for f in filenames_json
            ]

            # check for entity mismatches and use first one working
            for file in file_entities_json:
                if check_entity_mismatch(file, entities):
                    # load .json file and save it
                    columns = parse_json_sidecar(
                        folder / (file + f"_{file_ending}.json")
                    )
                    break
        else:
            break

    for folder in folders_tsv:
        if events == []:
            # get all possible files with _events.tsv
            files_tsv = list(folder.glob(f"*_{file_ending}.tsv"))
            files_tsv.extend(list(folder.glob(f"*_{file_ending}.tsv.gz")))
            filenames_tsv = [f.stem.removesuffix(f"_{file_ending}") for f in files_tsv]

            # check for entity mismatches and use first one working
            for file in filenames_tsv:
                if check_entity_mismatch(file, entities):
                    # load .tsv file and save it
                    try:
                        data = parse_descriptive_tsv(
                            tsv_path=folder / (file + f"_{file_ending}.tsv")
                        )
                    except FileNotFoundError:
                        data = parse_descriptive_tsv(
                            tsv_path=folder / (file + f"_{file_ending}.tsv.gz")
                        )
                    for event in data:
                        add_object_to_sequence(
                            entity_list=events,
                            entity_class=Event,
                            **event,
                            columns=columns,
                        )
                    break
        else:
            break

    return events


def get_stims_from_files(
    cls: Run, base_path: os.PathLike | str
) -> dict[str, StimRecording] | None:
    base_path = pathlib.Path(base_path)

    stims = {}

    # possibility 1:
    #   multiple recordings exist
    # possibility 2
    #   one recording exists (with recording label)
    #   or without recording label
    rec_labels = get_recordings_from_files(
        run=cls, base_path=base_path, file_ending="stim"
    )
    if rec_labels:
        files_json = base_path.glob("*_stim.json")
        files_tsv = base_path.glob("*_stim.tsv.gz")

        for key, value in rec_labels.items():
            # get description (load json sidecar)
            entitylist = cls.get_top_level_entities()
            entitylist.append(key)

            description = {}
            for file in files_json:
                if check_entity_mismatch(
                    file.stem.removesuffix("_stim"),
                    entitylist,
                ):
                    description = parse_json_sidecar(file)
            for file in files_tsv:
                if check_entity_mismatch(
                    file.stem.removesuffix("_stim"),
                    entitylist,
                ):
                    data = load_tsv_data(file)

            # create the entity with the loaded description
            if description:
                description = manipulate_dictkeys(description, to_snakecase)
                # TODO create hardware and columns as class
                stims[key] = StimRecording(
                    virtual_entity=value,
                    recording_id=key,
                    base_path=base_path,
                    **description,
                    **data,
                )
            else:
                raise FileNotFoundError

    # possibility 3
    #   one recording in higher directory
    else:
        entities = cls.get_top_level_entities()
        folders = [base_path]
        path = base_path
        target = entities[0]
        while path.name != target:
            path = path.parent
            folders.append(path)
        path = path.parent
        folders.append(path)

        description = {}
        data = pd.DataFrame()
        exists = False
        # if stims is in higher folder only one file can exist
        for folder in folders:
            if description == {}:
                # get all possible files with _stim.json
                files_json = folder.glob("*_stim.json")
                files_tsv = folder.glob("*_stim.tsv.gz")

                # check for entity mismatches and use first one working
                for file in files_json:  # in this case no recording label exists
                    if check_entity_mismatch(
                        file.stem.removesuffix("_stim"), cls.get_top_level_entities()
                    ):
                        # load .json file and save it
                        description = parse_json_sidecar(file)
                        exists = True
                        break

                for file in files_tsv:
                    if check_entity_mismatch(
                        file.stem.removesuffix("_stim"),
                        cls.get_top_level_entities(),
                    ):
                        data = load_tsv_data(file)
                        exists = True
                        break
            else:
                break
        if exists:
            description = manipulate_dictkeys(description, to_snakecase)
            stims["recording-00"] = StimRecording(
                virtual_entity=True,
                recording_id="recording-00",
                base_path=base_path,
                **description,
                **data,
            )

    return stims


def write_events_to_files(
    cls: Recording | Run,
    events: Sequence[Event],
    output_path: os.PathLike | str,
    file_ending="events",
    compressed=False,
) -> None:
    output_path_json = append_path(output_path, f"_{file_ending}.json")
    if compressed:
        output_path_tsv = append_path(output_path, f"_{file_ending}.tsv.gz")
    else:
        output_path_tsv = append_path(output_path, f"_{file_ending}.tsv")

    data_json = events[0].columns
    data_tsv = pd.DataFrame(event.__dict__ for event in events)
    data_tsv = data_tsv.drop(columns=["columns"], errors="ignore")

    if "stim_file" in data_tsv.columns:  # TODO
        # find root of the dataset
        entities = cls.get_top_level_entities()
        output_dataset_root = pathlib.Path(output_path)
        target = entities[0]
        while output_dataset_root.name != target:
            output_dataset_root = output_dataset_root.parent
        output_dataset_root = output_dataset_root.parent

        dataset_root = cls.root
        while dataset_root.name != target:
            dataset_root = dataset_root.parent
        dataset_root = dataset_root.parent
        # create stimuli directory
        stimuli_path = pathlib.Path(output_dataset_root / "stimuli")
        if not stimuli_path.exists():
            stimuli_path.mkdir(parents=True, exist_ok=True)

        # copy files into the stimuli directory
        unique_files = set(data_tsv["stim_file"])
        for file in unique_files:
            copy_file(
                source_path=dataset_root / "stimuli" / str(file),
                destination_path=stimuli_path,
            )

    if isinstance(data_json, dict):
        write_json(content=data_json, output_path=output_path_json)
    if compressed:
        data_tsv.to_csv(
            output_path_tsv, sep="\t", index=False, header=True, compression="gzip"
        )
    else:
        data_tsv.to_csv(output_path_tsv, sep="\t", index=False, header=True)
