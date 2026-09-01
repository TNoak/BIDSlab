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

from abidskit._typing import A
from abidskit.common.base import BaseAcquisition, Entity, Event
from abidskit.settings import get_settings_value
from abidskit.utils.checks import check_if_valid_uri
from abidskit.utils.exceptions import (
    FieldEntryNotValidError,
    TopLevelEntityNotLinkedWarning,
)
from abidskit.utils.helpers import (
    add_object_to_sequence,
    append_path,
    check_entity_mismatch,
    get_entity_from_file,
    get_tsv_json_files,
    load_tsv_data,
    parse_descriptive_tsv,
    parse_json_sidecar,
    set_attr_from_dict,
    write_json,
)
from abidskit.utils.string_manipulation import to_snakecase

if TYPE_CHECKING:
    from abidskit.common.specs_task import Task

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


class Recording(Entity):
    def __init__(
        self,
        base_path: os.PathLike | str,
        recording_id: str,
        sampling_frequency: int | float,
    ):
        super().__init__(_entity_id=recording_id, _entity_name="recording")
        self.recording_id: str = self._entity_id
        self.sampling_frequency: int | float = sampling_frequency

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._data: Any = None

        self._run: Run | None = None

    @property
    def run(self) -> "Run | None":
        if self._run:
            return self._run

        warn("Recording is not linked to a Run object.", TopLevelEntityNotLinkedWarning)
        return self._run

    @run.setter
    def run(self, value: "Run") -> None:
        self._run = value

    @property
    def data(self):
        if self._data is None:
            # TODO: Rewrite to generalize for other data types than motion
            file_name = "*"
            # file_name = f"*{self.acquisition.tracking_system.tracking_system_id}*"
            # file_name += (
            #     f"_{self.acquisition.acquisition_id}"
            #     if len(self.acquisition.tracking_system.acquisitions) > 1
            #     else ""
            # )
            file_name += (
                f"_{self.run.run_id}" if len(self.run.acquisition.runs) > 1 else ""
            )
            file_name += f"_{self.recording_id}" if len(self.run.physio) > 1 else ""
            tsv_path, _ = get_tsv_json_files(
                self.run.root,
                file_name + "_physio",
            )
            data_frame = load_tsv_data(path=tsv_path, header=None)
            column_names = {}
            for column_number, column in enumerate(self.columns):
                column_names[column_number] = column.column_name
            data_frame.rename(columns=column_names, inplace=True)

            self._data = data_frame

        return self._data

    @data.setter
    def data(self, value: pd.DataFrame) -> None:
        self._data = value

    def write(self, output_path: os.PathLike | str) -> None:
        # TODO: implement writing of basic Recording data
        if not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
            raise NotImplementedError


class PhysioRecording(Recording):
    def __init__(
        self,
        base_path: os.PathLike | str,
        recording_id: str,
        sampling_frequency: int,
        start_time: int | float,
        columns: MutableSequence[Column],
        hardware: Hardware | None = None,
    ):
        super().__init__(
            base_path=base_path,
            recording_id=recording_id,
            sampling_frequency=sampling_frequency,
        )

        self.start_time: int | float = start_time
        self.columns: MutableSequence[Column] = columns
        self.hardware: Hardware | None = hardware


class Run(Entity, Generic[A]):
    def __init__(self, base_path: os.PathLike | str, run_id: int, **kwargs: Any):
        if not isinstance(run_id, int):
            raise TypeError("run_id must be an index of type integer")
        run_id_str = str(run_id)
        super().__init__(_entity_id=run_id_str, _entity_name="run")
        self.run_id: str = self._entity_id

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._acquisition: A | None = None

        self._physio: Sequence[PhysioRecording] | None = None
        self._events: Sequence[Event] | None = None

        set_attr_from_dict(self, kwargs)

    def __repr__(self):
        return f"Run id=run-{self.run_id}"

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
    def physio(self):
        if not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
            raise NotImplementedError
        # if not self._physio:
        #     self._physio = []
        #     files = self.root.iterdir()
        #     physio_rec_ids = set()
        #     for file in files:
        #         try:
        #             physio_rec_ids.add(
        #                 get_entity_from_file(
        #                     file,
        #                     "recording",
        #                 )["recording"]
        #             )
        #         except KeyError:
        #             continue
        #     for rec_id in physio_rec_ids:
        #         _, json_path = get_tsv_json_files(
        #             self.root,
        #             f"*_{self.run_id}_{rec_id}_physio",
        #         )
        #         if json_path:
        #             data = parse_json_sidecar(json_path)
        #
        #             self._physio.append(
        #                 PhysioRecording(
        #                     recording_id=rec_id,
        #                     sampling_frequency=data.get("SamplingFrequency"),
        #                     start_time=data.get("StartTime"),
        #                     columns=data.get("Columns"),
        #                 )
        #             )
        #
        # return self._physio

    @physio.setter
    def physio(self, value: Sequence[dict] | Sequence[PhysioRecording]):
        if not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
            raise NotImplementedError

    @property
    def events(self):
        # TODO json sidecar may be in higher directory levels
        # TODO create stimuli folder if respective column exists
        if self._events is None:
            # get list of top level entities
            entities = self.get_top_level_entities()

            # get all possible files with _events.json
            files_json = list(self.root.glob("*_events.json"))
            filenames_json = [f.name for f in files_json]
            file_entities_json = [
                f.removesuffix("_events.json") for f in filenames_json
            ]

            columns = []
            # check for entity mismatches and use first one working
            for file in file_entities_json:
                if check_entity_mismatch(file, entities):
                    # load .json file and save it
                    columns = parse_json_sidecar(self.root / (file + "_events.json"))
                    break

            # get all possible files with _events.tsv
            files_tsv = list(self.root.glob("*_events.tsv"))
            filenames_tsv = [f.name for f in files_tsv]
            file_entities_tsv = [f.removesuffix("_events.tsv") for f in filenames_tsv]

            data = []
            # check for entity mismatches and use first one working
            for file in file_entities_tsv:
                if check_entity_mismatch(file, entities):
                    # load .tsv file and save it
                    data = parse_descriptive_tsv(
                        tsv_path=self.root / (file + "_events.tsv")
                    )
                    self._events = []
                    for event in data:
                        add_object_to_sequence(
                            entity_list=self._events,
                            entity_class=Event,
                            **event,
                            columns=columns,
                        )
                    break

        return self._events

    @events.setter
    def events(self, value: Sequence[Event]) -> None:
        self._events = value

    def get_top_level_entities(self) -> list[str | Any]:
        assert self.acquisition is not None
        entities = self.acquisition.get_top_level_entities()
        entities.append(self.run_id)
        return entities

    def write(self, output_path: os.PathLike | str) -> None:
        output_path_json = append_path(output_path, "_events.json")
        output_path_tsv = append_path(output_path, "_events.tsv")

        if self.events:
            data_json = self.events[0].columns
            data_tsv = pd.DataFrame(event.__dict__ for event in self.events)
            data_tsv = data_tsv.drop(columns=["columns"], errors="ignore")

            if isinstance(data_json, dict):
                write_json(content=data_json, output_path=output_path_json)
            data_tsv.to_csv(output_path_tsv, sep="\t", index=False, header=True)


class Acquisition(BaseAcquisition):
    def __init__(self, base_path: os.PathLike | str, acquisition_id: str):
        super().__init__(base_path=base_path, acquisition_id=acquisition_id)

        self._task: Task | None = None

    @property
    def runs(self) -> dict[int, Run]:
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
                        run_id: Run(
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
                        0: Run(
                            run_id=0,
                            base_path=self.root,
                            acquisition=self,
                        )
                    }
                )

        return self._runs

    @runs.setter
    def runs(self, value: Sequence[int | Run] | dict[int, Run]) -> None:
        if isinstance(value, Sequence):
            if all(isinstance(entry, int) for entry in value):
                self._runs = {}
                for entry in value:
                    assert isinstance(entry, int)  # for mypy
                    self._runs.update(
                        {
                            entry: Run(
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
