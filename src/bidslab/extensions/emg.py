#  Copyright (c) 2026 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import json
import os
import pathlib
import re
from dataclasses import asdict, dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from warnings import warn

import pandas as pd

from bidslab.common.base import BaseAcquisition, BaseTask, check_entity_mismatch
from bidslab.common.specs_misc import (
    Column,
    Event,
    Filter,
    Hardware,
    Institution,
    Recording,
    Run,
    get_events_from_files,
    write_events_to_files,
)
from bidslab.utils.dict_manipulation import ManipulateKeysOption, clean_dict
from bidslab.utils.exceptions import (
    FieldEntryNotValidError,
    FieldMissingError,
    FileNotFoundWarning,
    TopLevelEntityNotLinkedWarning,
)
from bidslab.utils.helpers import (
    add_object_to_sequence,
    append_path,
    get_edf_json_files,
    get_entity_from_file,
    get_tsv_json_files,
    load_edf_data,
    parse_descriptive_tsv,
    parse_json_sidecar,
    set_attr_from_dict,
    write_entities,
    write_json,
)
from bidslab.utils.string_manipulation import to_snakecase

if TYPE_CHECKING:
    from bidslab.common import Datatype

EMG_CHANNEL_TYPE_ALLOWED_FIELD_ENTRIES = {
    "ECG",
    "EMG",
    "EOG",
    "HEOG",
    "LATENCY",
    "MISC",
    "REF",
    "SYSCLOCK",
    "TRIG",
    "VEOG",
}


@dataclass(slots=True)
class EMGHardware(Hardware):
    electrode_manufacturer: str | None = None
    electrode_manufacturers_model_name: str | None = None


@dataclass(slots=True)
class EMGCoordinateSystem:
    name: str
    emg_coordinate_system: str
    emg_coordinate_units: str
    emg_coordinate_system_description: str | None = None
    parent_coordinate_system: str | None = None
    anchor_coordinates: Sequence[int | float] | None = None
    anchor_electrode: str | None = None

    def __post_init__(self):
        if (
            self.emg_coordinate_system == "Other"
            and not self.emg_coordinate_system_description
        ):
            raise FieldMissingError(
                "Field `EMGCoordinateSystemDescription` must be present if field "
                "`EMGCoordinateSystem` is 'Other'"
            )
        if self.parent_coordinate_system:
            if not self.anchor_coordinates:
                raise FieldMissingError(
                    "Field `AnchorCoordinates` must be present if field "
                    "`ParentCoordinateSystem` is present"
                )
            if not self.anchor_electrode:
                raise FieldMissingError(
                    "Field `AnchorElectrode` must be present if field "
                    "`ParentCoordinateSystem` is present"
                )

    def __repr__(self) -> str:
        return f"<EMGCoordinateSystem name={self.name}>"

    def __hash__(self) -> int:
        return id(self)


class EMGChannel:
    def __init__(
        self,
        name: str,
        type: str,  # noqa: A002
        units: str,
        **kwargs: Any,
    ):
        self.name: str = name
        self._type: str = type
        self.units: str = units
        self.description: str | None = None
        self.sampling_frequency: int | float | None = None
        self.signal_electrode: str | None = None
        self.reference: str | None = None
        self.group: str | int | float | None = None
        self.target_muscle: str | None = None
        self.placement_scheme: str | None = None
        self.placement_description: str | None = None
        self.interelectrode_distance: int | float | None = None
        self.low_cutoff: int | float | None = None
        self.high_cutoff: int | float | None = None
        self.notch: str | None = None
        self.status: str | None = None
        self.status_description: str | None = None
        self.columns: Sequence[Column] | None = None

        set_attr_from_dict(self, kwargs)

    def __repr__(self) -> str:
        return f"<EMGChannel name={self.name}>"

    @property
    def type(self) -> str | None:
        return self._type

    @type.setter  # noqa: A003
    def type(self, value: str) -> None:
        if value not in EMG_CHANNEL_TYPE_ALLOWED_FIELD_ENTRIES:
            raise FieldEntryNotValidError(
                f"Field `Type` must be one of {EMG_CHANNEL_TYPE_ALLOWED_FIELD_ENTRIES}"
            )
        self._type = value


class EMGElectrode:
    def __init__(
        self,
        name: str,
        x: int | float,
        y: int | float,
        **kwargs: Any,
    ):
        self.name: str = name
        self.x: int | float = x
        self.y: int | float = y
        self.z: int | float | None = None
        self.coordinate_system: EMGCoordinateSystem | None = None
        self.type: str | None = None
        self.material: str | None = None
        self.impedance: int | float | None = None
        self.group: str | int | float | None = None
        self.columns: Sequence[Column] | None = None

        set_attr_from_dict(self, kwargs)

    def __repr__(self) -> str:
        return f"<EMGElectrode name={self.name}>"


class EMGRecording(Recording):
    def __init__(
        self,
        base_path: os.PathLike | str,
        recording_id: str,
        sampling_frequency: int | float,
        emg_placement_scheme: str,
        emg_reference: str,
        power_line_frequency: int | float | str,
        recording_type: str,
        software_filters: MutableMapping[str, Filter] | str,
        virtual_entity: bool = False,
        **kwargs: Any,
    ):
        # TODO: filters should be filter objects
        description = kwargs.pop("_description", None)
        if description is not None and not isinstance(description, MutableMapping):
            raise TypeError(
                "Parameter type for argument `_description` must be MutableMapping"
            )
        self._description: MutableMapping | None = description

        super().__init__(
            base_path=base_path,
            recording_id=recording_id,
            sampling_frequency=sampling_frequency,
            virtual_entity=virtual_entity,
        )

        self.emg_placement_scheme: str = emg_placement_scheme
        if self.emg_placement_scheme != "Other":
            self.emg_placement_scheme_description: str | None = None
        else:
            try:
                self.emg_placement_scheme_description = kwargs.pop(
                    "emg_placement_scheme_description"
                )
            except KeyError:
                raise FieldMissingError(
                    "Field `EMGPlacementSchemeDescription` must be present if field "
                    "`EMGPlacementScheme` is 'Other'"
                ) from None
        self.emg_reference: str = emg_reference
        self.power_line_frequency: int | float | str = power_line_frequency
        self.recording_type: str = recording_type
        self.software_filters: MutableMapping[str, Filter] | str = software_filters
        self.emg_channel_count: int | None = None
        self.hardware_filters: MutableMapping[str, Filter] | str | None = None
        self.recording_duration: int | float | None = None
        self.electrode_material: str | None = None
        self.electrode_type: str | None = None
        self.emg_ground: str | None = None
        self.epoch_length: int | float | None = None
        self.gain: int | float | None = None
        self.interelectrode_distance: int | float | None = None
        self.preamplification: int | float | None = None
        self.skin_preparation: str | None = None
        self.subject_artefact_description: str | None = None
        self.trigger_channel_count: int | None = None

        self._hardware: EMGHardware | None = None
        self._institution: Institution | None = None

        self._electrodes: MutableSequence[EMGElectrode] | None = None
        self._channels: MutableSequence[EMGChannel] | None = None
        self._coordinate_systems: MutableSequence[EMGCoordinateSystem] | None = None

        self._events: Sequence[Event] | None = None

        self._run: "EMGRun | None" = None

        # Try to set attributes from arguments
        set_attr_from_dict(self, kwargs)

        self._update_description()

        # Update values from self._description
        if self._description:
            emg_description = self._description.pop("emg", {})
            _ = self._description.pop("task", None)
            set_attr_from_dict(self, {**self._description, **emg_description})

    def __repr__(self) -> str:
        return f"<Recording id={self.recording_id}>"

    @property
    def hardware(self) -> EMGHardware | None:
        return self._hardware

    @hardware.setter
    def hardware(self, value: Mapping | EMGHardware) -> None:
        if isinstance(value, Mapping):
            hardware_data = {}
            for k, v in value.items():
                hardware_data[to_snakecase(k)] = v
            self._hardware = EMGHardware(**hardware_data)
        elif isinstance(value, EMGHardware):
            self._hardware = value
        else:
            raise TypeError("Field `Hardware` must be an EMGHardware object")

    @property
    def institution(self) -> Institution | None:
        return self._institution

    @institution.setter
    def institution(self, value: Mapping | Institution) -> None:
        if isinstance(value, Mapping):
            institution_data = {}
            for k, v in value.items():
                institution_data[to_snakecase(k)] = v
            self._institution = Institution(**institution_data)
        elif isinstance(value, Institution):
            self._institution = value
        else:
            raise TypeError("Field `Institution` must be an Institution object")

    @property
    def channels(self) -> MutableSequence[EMGChannel] | None:
        return self._channels

    @channels.setter
    def channels(self, value: MutableSequence[Mapping | EMGChannel]) -> None:
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, Mapping) for entry in value):
                self._channels = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._channels.append(EMGChannel(**entry))
            elif all(isinstance(entry, EMGChannel) for entry in value):
                self._channels = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Channels` must be a list of EMGChannel object")

    @property
    def electrodes(self) -> MutableSequence[EMGElectrode] | None:
        return self._electrodes

    @electrodes.setter
    def electrodes(self, value: MutableSequence[Mapping | EMGElectrode]) -> None:
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, Mapping) for entry in value):
                self._electrodes = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._electrodes.append(EMGElectrode(**entry))
            elif all(isinstance(e, EMGElectrode) for e in value):
                self._electrodes = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Electrodes` must be a list of EMGElectrodes object")

    @property
    def coordinate_systems(self) -> MutableSequence[EMGCoordinateSystem] | None:
        if self._coordinate_systems is None:
            self._coordinate_systems = []
            # TODO load corrdsystems from files
            entities = self.get_top_level_entities()

            # get all possible files with _coordsystem.json
            files_json = list(self.root.glob("*_coordsystem.json"))
            filenames_json = [f.name for f in files_json]
            file_entities_json = [
                f.removesuffix("_coordsystem.json") for f in filenames_json
            ]

            # check for entity mismatches and use first one working
            for file in file_entities_json:
                if check_entity_mismatch(file, entities):
                    # load .json file and save it
                    data = parse_json_sidecar(self.root / (file + "_coordsystem.json"))
                    data = clean_dict(data, string_manipulation=to_snakecase)
                    # get the name (space-<name>) from the filename
                    nameparts = file.split("_")
                    name_dict = {
                        namepart.split("-")[0]: namepart.split("-")[1]
                        for namepart in nameparts
                    }
                    name = name_dict.pop("space", "")
                    self._coordinate_systems.append(
                        EMGCoordinateSystem(
                            name=name,
                            emg_coordinate_system=data.pop("emg_coordinate_system"),
                            emg_coordinate_units=data.pop("emg_coordinate_units"),
                            **data,
                        )
                    )

        return self._coordinate_systems

    @coordinate_systems.setter
    def coordinate_systems(self, value: MutableSequence[EMGCoordinateSystem]) -> None:
        self._coordinate_systems = value

    @property
    def data(self):
        if self._data is None:
            file_name = f"*{self.run.acquisition.task.task_id}*"
            file_name += (
                f"_{self.run.acquisition.acquisition_id}"
                if not self.run.acquisition._virtual_entity
                else ""
            )
            file_name += f"_{self.run.run_id}" if not self.run._virtual_entity else ""
            file_name += f"_{self.recording_id}" if not self._virtual_entity else ""
            edf_path, _ = get_edf_json_files(
                self.root,
                file_name + "_emg",
            )
            data_frame = load_edf_data(path=edf_path)
            column_names = {}
            for channel_number, channel in enumerate(self.channels):
                column_names[channel_number] = channel.name
            data_frame.rename(columns=column_names, inplace=True)

            self._data = data_frame

        return self._data

    @data.setter
    def data(self, value: pd.DataFrame) -> None:
        self._data = value

    @property
    def events(self) -> Sequence[Event] | None:
        if self._events is None:
            self._events = get_events_from_files(self, self.root)

        return self._events

    @events.setter
    def events(self, value: Sequence[Event]) -> None:
        self._events = value

    def _update_description(self) -> None:
        file_name = f"*_{self.recording_id}_"
        _update_description_data(self, file_name)

    def write(self, output_path):
        # write events files
        if self.events:
            write_events_to_files(self, self.events, output_path)

        # TODO write data files (_emg.bdf/edf/+)
        # usual path

        # TODO write json sidecar (_emg.json)
        # usual path

        # TODO write channels files (_channels.json, _channels.tsv)
        # usual path
        if self.channels:
            output_path_channels_json = append_path(output_path, "_channels.json")
            output_path_channels_tsv = append_path(output_path, "_channels.tsv")

            channels_dataframe = self.list_channels()
            channels_dataframe.to_csv(output_path_channels_tsv, sep="\t", index=False)

            # TODO write channels description (.json)

        # TODO write electrodes files (_electrodes.tsv, _electrodes.json)
        # usual path
        if self.electrodes:
            output_path_electrodes_json = append_path(output_path, "_electrodes.json")
            output_path_electrodes_tsv = append_path(output_path, "_electrodes.tsv")

            electrodes_dataframe = self.list_electrodes()
            electrodes_dataframe.to_csv(
                output_path_electrodes_tsv, sep="\t", index=False
            )

            # TODO write electrodes description (.json)

        # write coordinate system files (_coordsystem.json)
        # path may contain space entity before recoring
        if self.coordinate_systems:
            for coordsystem in self.coordinate_systems:
                # build correct output path (order of entities)
                if coordsystem.name != "":
                    if self.virtual_entity:
                        output_path_coordsystem = append_path(
                            output_path, f"_space-{coordsystem.name}_coordsystem.json"
                        )
                    else:
                        filename = output_path.name
                        filename.split("_")
                        filename.append(filename[-1])
                        filename[-1] = f"space-{coordsystem.name}"
                        name = ""
                        name = (name + "_" + part for part in filename)
                        name = name + "_coordsystem.json"
                        output_path_coordsystem = append_path(output_path.parent, name)
                else:
                    output_path_coordsystem = append_path(
                        output_path, "_coordsystem.json"
                    )

                coord_dict = asdict(coordsystem)
                _ = coord_dict.pop("name", None)
                coord_dict = clean_dict(coord_dict)
                write_json(coord_dict, output_path=output_path_coordsystem)

        # TODO write photo files if available (_photo.jpg/png/tif)
        # path can only contain sub, ses, acq, recording

    def list_channels(self) -> pd.DataFrame:
        channels_dataframe = pd.DataFrame()
        for emg_channel in self.channels if self.channels else []:
            channel_dict = emg_channel.__dict__.copy()
            channel_dict["component"] = channel_dict.pop("_component", None)
            channel_dict["type"] = channel_dict.pop("_type", None)

            coordinate_system = channel_dict.pop("coordinate_system", None)
            if isinstance(coordinate_system, EMGCoordinateSystem):
                channel_dict["coordinate_system"] = coordinate_system.name
            elif coordinate_system:
                channel_dict["coordinate_system"] = coordinate_system

            channel_dict.pop("columns")

            channel_dict = clean_dict(channel_dict)
            channels_dataframe = pd.concat(
                [channels_dataframe, pd.DataFrame([channel_dict])],
                ignore_index=True,
            )
        channels_dataframe.dropna(axis=1, how="all", inplace=True)
        return channels_dataframe

    def list_electrodes(self) -> pd.DataFrame:
        electrodes_dataframe = pd.DataFrame()
        for emg_electrode in self.electrodes if self.electrodes else []:
            electrode_dict = emg_electrode.__dict__.copy()

            coordinate_system = electrode_dict.pop("coordinate_system", None)
            if isinstance(coordinate_system, EMGCoordinateSystem):
                electrode_dict["coordinate_system"] = coordinate_system.name

            electrode_dict.pop("columns")

            electrode_dict = clean_dict(electrode_dict)
            electrodes_dataframe = pd.concat(
                [electrodes_dataframe, pd.DataFrame([electrode_dict])],
                ignore_index=True,
            )
        electrodes_dataframe.dropna(axis=1, how="all", inplace=True)
        return electrodes_dataframe


class EMGRun(Run):
    def __init__(
        self,
        base_path: os.PathLike | str,
        run_id: int,
        virtual_entity: bool = False,
        **kwargs: Any,
    ):
        description = kwargs.pop("_description", {})
        if not isinstance(description, MutableMapping):
            raise TypeError(
                "Parameter type for argument `_description` must be MutableMapping"
            )
        self._description: MutableMapping = description

        super().__init__(
            base_path=base_path, run_id=run_id, virtual_entity=virtual_entity, **kwargs
        )

        self._recordings: dict[str, EMGRecording] | None = None

        self._update_description()

    # def __repr__(self) -> str:
    #     return f"<Run id=run-{self.run_id}>"

    @property
    def recordings(self) -> dict[str, EMGRecording] | None:
        if not self._recordings:
            # TODO make this more elegant
            assert self.acquisition is not None
            file_name = f"*{self.acquisition.task.task_id}"
            file_name += (
                f"_{self.acquisition.acquisition_id}"
                if not self.acquisition._virtual_entity
                else ""
            )
            file_name += f"_{self.run_id}" if not self._virtual_entity else ""

            self._recordings = {}
            files = self.root.glob("*_emg.*")
            recording_labels = set()
            for file in files:
                try:
                    recording_labels.add(
                        get_entity_from_file(
                            file,
                            "recording",
                        )["recording"]
                    )
                except KeyError:
                    continue

            # values in self._description get passed forward as fallback / to follow the
            # inheritance principle of BIDS but will be updated downstream
            for recording_label in recording_labels:
                self._recordings.update(
                    {
                        "recording-" + recording_label: EMGRecording(
                            recording_id="recording-" + recording_label,
                            base_path=self.root,
                            run=self,
                            hardware=self._description.get("hardware", None),
                            institution=self._description.get("institution", None),
                            channels=get_emg_channels(
                                *get_tsv_json_files(
                                    self.root,
                                    file_name
                                    + f"_recording-{recording_label}_channels",
                                )
                            ),
                            electrodes=self._description.get("electrodes", None),
                            **self._description.get("emg", None),
                        )
                    }
                )

            # If no recordings are found, add a default one
            if not self._recordings:
                self._recordings.update(
                    {
                        "recording-00": EMGRecording(
                            recording_id="recording-00",
                            base_path=self.root,
                            run=self,
                            hardware=self._description.get("hardware", None),
                            institution=self._description.get("institution", None),
                            channels=get_emg_channels(
                                *get_tsv_json_files(
                                    self.root,
                                    file_name + "_channels",
                                )
                            ),
                            electrodes=self._description.get("electrodes", None),
                            virtual_entity=True,
                            **self._description.get("emg", None),
                        )
                    }
                )

        return self._recordings

    @recordings.setter
    def recordings(self, value: MutableSequence[MutableMapping | EMGRecording]) -> None:
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, MutableMapping) for entry in value):
                self._recordings = {}
                for entry in value:
                    assert isinstance(entry, MutableMapping)  # for mypy
                    assert isinstance(entry["recording_id"], str)
                    self._recordings.update(
                        {
                            entry["recording_id"]: EMGRecording(
                                base_path=self.root,
                                run=self,
                                **entry,
                            )
                        }
                    )
            elif all(isinstance(entry, EMGRecording) for entry in value):
                self._recordings = {}
                for entry in value:
                    assert isinstance(entry, EMGRecording)
                    assert isinstance(entry.recording_id, str)
                    self._recordings.update({entry.recording_id: entry})
        else:
            raise TypeError(
                "Field `Recordings` must be a list of EMGRecordings objects"
            )

    def _update_description(self) -> None:
        file_name = f"*_{self.run_id}_*"
        _update_description_data(self, file_name)

    def write(self, output_path: os.PathLike | str) -> None:
        super().write(output_path)
        assert self.recordings is not None
        write_entities(output_path, self.recordings.values())
        # TODO what needs to be done with self.description?


class EMGAcquisition(BaseAcquisition):
    def __init__(
        self,
        base_path: os.PathLike | str,
        acquisition_id: str,
        task: "EMGTask",
        virtual_entity: bool = False,
        **kwargs: Any,
    ):
        description = kwargs.pop("_description", {})
        if not isinstance(description, MutableMapping):
            raise TypeError(
                "Parameter type for argument `_description` must be MutableMapping"
            )
        self._description: MutableMapping = description

        super().__init__(
            base_path=base_path,
            acquisition_id=acquisition_id,
            virtual_entity=virtual_entity,
        )

        self._task: "EMGTask | None" = task

        self._update_description()

        set_attr_from_dict(self, kwargs)

    @property
    def runs(self) -> dict[str, EMGRun]:
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
                self._runs.update(
                    {
                        "run-" + run_id: EMGRun(
                            run_id=int(run_id),
                            base_path=self.root,
                            acquisition=self,
                            _description=self._description,
                        )
                    }
                )

            # If no runs are found, add a default one
            if not self._runs:
                self._runs.update(
                    {
                        "run-0": EMGRun(
                            run_id=0,
                            base_path=self.root,
                            acquisition=self,
                            _description=self._description,
                            virtual_entity=True,
                        )
                    }
                )

        return self._runs

    @runs.setter
    def runs(self, value: MutableSequence[int | EMGRun] | dict[str, EMGRun]) -> None:
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, int) for entry in value):
                self._runs = {}
                for entry in value:
                    assert isinstance(entry, int)  # for mypy
                    self._runs.update(
                        {
                            f"run-{entry}": EMGRun(
                                run_id=entry,
                                base_path=self.root,
                                acquisition=self,
                                _description=self._description,
                            )
                        }
                    )
            elif all(isinstance(v, EMGRun) for v in value):
                self._runs = {}
                for v in value:
                    assert isinstance(v, EMGRun)
                    assert isinstance(v.run_id, str)
                    self._runs.update({v.run_id: v})
        elif isinstance(value, dict):
            self._runs = value
        else:
            raise TypeError("Field `Runs` must be a list of EMGRun objects")

    @property
    def task(self) -> "EMGTask | None":
        if self._task:
            return self._task

        warn(
            "Acquisition is not linked to a EMGTask object.",
            TopLevelEntityNotLinkedWarning,
        )
        return self._task

    @task.setter
    def task(self, value: "EMGTask") -> None:
        self._task = value

    def _update_description(self) -> None:
        if self._virtual_entity:
            assert self.task is not None
            file_name = f"*_{self.task.task_id}_*"
        else:
            file_name = f"*_{self.acquisition_id}_*"
        _update_description_data(self, file_name)

    def get_top_level_entities(self) -> list[str | Any]:
        assert self.task is not None
        entities = self.task.get_top_level_entities()
        entities.append(self.acquisition_id)
        return entities


class EMGTask(BaseTask):
    def __init__(
        self,
        base_path: os.PathLike | str,
        task_name: str,
        **kwargs: "str | Datatype | MutableSequence | MutableMapping",
    ) -> None:
        description = kwargs.pop("_description", {})
        if not isinstance(description, MutableMapping):
            raise TypeError(
                "Parameter type for argument `_description` must be MutableMapping"
            )
        self._description: MutableMapping = description

        super().__init__(
            base_path=base_path, task_name=task_name, virtual_entity=False, **kwargs
        )

        self._acquisitions: dict[str, EMGAcquisition] | None = None

    @property
    def acquisitions(self) -> dict[str, EMGAcquisition]:
        if not self._acquisitions:
            self._acquisitions = {}
            files = self.root.iterdir()
            acquisition_labels = set()
            for file in files:
                try:
                    acquisition_labels.add(
                        get_entity_from_file(
                            file,
                            "acq",
                        )["acq"]
                    )
                except KeyError:
                    continue
            for acquisition_label in acquisition_labels:
                self._acquisitions.update(
                    {
                        "acq-" + acquisition_label: EMGAcquisition(
                            acquisition_id="acq-" + acquisition_label,
                            base_path=self.root,
                            task=self,
                            _description=self._description,
                        )
                    }
                )

            # If no acquisitions are found, add a default one
            if not self._acquisitions:
                self._acquisitions.update(
                    {
                        "acq-00": EMGAcquisition(
                            acquisition_id="acq-00",
                            base_path=self.root,
                            task=self,
                            _description=self._description,
                            virtual_entity=True,
                        )
                    }
                )

        return self._acquisitions

    @acquisitions.setter
    def acquisitions(
        self, value: MutableSequence[str] | MutableSequence[EMGAcquisition]
    ) -> None:
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, str) for entry in value):
                self._acquisitions = {}
                for entry in value:
                    assert isinstance(entry, str)  # for mypy
                    self._acquisitions.update(
                        {
                            entry: EMGAcquisition(
                                acquisition_id=entry,
                                base_path=self.root,
                                task=self,
                                _description=self._description,
                            )
                        }
                    )
            elif all(isinstance(entry, EMGAcquisition) for entry in value):
                self._acquisitions = {}
                for entry in value:
                    assert isinstance(entry, EMGAcquisition)
                    assert isinstance(entry.acquisition_id, str)
                    self._acquisitions.update({entry.acquisition_id: entry})
        else:
            raise TypeError(
                "Field `Acquisitions` must be a list of EMGAcquisition objects"
            )

    def write(self, output_path: os.PathLike | str) -> None:  # noqa: ARG002 TODO: Remove
        write_entities(output_path, self.acquisitions.values())
        # TODO check if right
        # where is json sidecar "*_emg.json" written? (recording)


def parse_emg_json_sidecar(sidecar_path: pathlib.Path) -> dict:
    with sidecar_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        task_description = {}
        hardware_description = {}
        institution_description = {}
        emg_description = {}
        for key, value in data.items():
            if re.match(r"^Task[A-Z].*|^Instructions", key):
                task_description[key] = value
            elif re.match(
                r"^Device[A-Z].*|^(Electrode)?Manufacturer.*|^SoftwareVersions", key
            ):
                hardware_description[key] = value
            elif re.match(r"^Institution.*", key):
                institution_description[key] = value
            else:
                emg_description[key] = value

        return {
            "task": task_description,
            "hardware": hardware_description,
            "institution": institution_description,
            "emg": emg_description,
        }


def get_emg_channels(
    tsv_path: pathlib.Path | None,
    json_path: pathlib.Path | None,
) -> MutableSequence[EMGChannel]:
    emg_channels: list[EMGChannel] = []
    columns = []

    if json_path:
        column_data = parse_json_sidecar(json_path)

        for column_name, column_values in column_data.items():
            columns.append(Column(name=column_name, **column_values))

    if tsv_path:
        data = parse_descriptive_tsv(tsv_path)
        for emg_channel in data:
            assert isinstance(emg_channel, dict), "Must be dicts in Generator."

            add_object_to_sequence(
                entity_list=emg_channels,
                entity_class=EMGChannel,
                columns=columns,
                **emg_channel,
            )

    return emg_channels


def get_emg_electrodes(
    tsv_path: pathlib.Path | None,
    json_path: pathlib.Path | None,
) -> MutableSequence[EMGElectrode]:
    emg_electrodes: list[EMGElectrode] = []
    columns = []

    if json_path:
        column_data = parse_json_sidecar(json_path)

        for column_name, column_values in column_data.items():
            columns.append(Column(name=column_name, **column_values))

    if tsv_path:
        data = parse_descriptive_tsv(tsv_path)
        for emg_electrode in data:
            assert isinstance(emg_electrode, dict), "Must be dicts in Generator."

            add_object_to_sequence(
                entity_list=emg_electrodes,
                entity_class=EMGElectrode,
                columns=columns,
                **emg_electrode,
            )

    return emg_electrodes


def _update_description_data(
    cls: EMGRecording | EMGRun | EMGAcquisition, file_name: str
):
    _, json_path = get_tsv_json_files(cls.root, file_name + "emg")

    if json_path:
        if not cls._description:
            data = parse_emg_json_sidecar(json_path)
            data_clean = clean_dict(
                data,
                skip_keys_to_manipulate=ManipulateKeysOption.ALL_KEYS_MANIPULATE,
                string_manipulation=to_snakecase,
            )
            cls._description = data_clean
        else:
            data = parse_emg_json_sidecar(json_path)
            data_clean = clean_dict(
                data,
                skip_keys_to_manipulate=ManipulateKeysOption.ALL_KEYS_MANIPULATE,
                string_manipulation=to_snakecase,
            )
            cls._description.update(data_clean)
    else:
        warn(
            f"No EMG JSON sidecar file found for {cls._entity_name} {cls._entity_id} "
            f"in {cls.root}",
            FileNotFoundWarning,
        )

    tsv_path, json_path = get_tsv_json_files(cls.root, file_name + "electrodes")
    if tsv_path:
        electrodes = {"electrodes": get_emg_electrodes(tsv_path, json_path)}
        if not cls._description:
            cls._description = electrodes
        else:
            cls._description.update(electrodes)
    else:
        warn(
            f"No EMG electrodes TSV and JSON sidecar file found for {cls._entity_name} "
            f"{cls._entity_id} in {cls.root}",
            FileNotFoundWarning,
        )
