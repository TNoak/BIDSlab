#  Copyright (c) 2025 by Lukas Behammer
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
from typing import Any, Mapping, MutableSequence
from warnings import warn

import pandas as pd

from abidskit.common.base import BaseAcquisition, BaseTask, Entity
from abidskit.common.specs_misc import Column, Hardware, Institution, Run
from abidskit.settings import get_settings_value
from abidskit.utils.dict_manipulation import clean_dict, delete_none_from_dict
from abidskit.utils.exceptions import (
    FieldEntryNotValidError,
    TopLevelEntityNotLinkedWarning,
)
from abidskit.utils.helpers import (
    add_object_to_sequence,
    append_path,
    get_entity_from_file,
    get_tsv_json_files,
    load_tsv_data,
    parse_descriptive_tsv,
    parse_json_sidecar,
    set_attr_from_dict,
    write_entities,
    write_json,
)
from abidskit.utils.string_manipulation import to_snakecase

MOTION_CHANNEL_COMPONENT_ALLOWED_FIELD_ENTRIES = {
    "x",
    "y",
    "z",
    "quat_x",
    "quat_y",
    "quat_z",
    "quat_w",
    "n/a",
}

MOTION_CHANNEL_TYPE_ALLOWED_FIELD_ENTRIES = {
    "ACCEL",
    "ANGACCEL",
    "GYRO",
    "JNTANG",
    "LATENCY",
    "MAGN",
    "MISC",
    "ORNT",
    "POS",
    "VEL",
}


@dataclass(slots=True)
class ReferenceFrame:
    name: str
    rotation_order: str | None = None
    rotation_rule: str | None = None
    spatial_axes: str | None = None
    description: str | None = None

    def __repr__(self) -> str:
        return f"<ReferenceFrame name={self.name}>"

    def __hash__(self) -> int:
        return id(self)


class MotionChannel:
    def __init__(
        self,
        name: str,
        component: str,
        type: str,  # noqa: A002
        tracked_point: str,
        units: str,
        **kwargs: Any,
    ):
        self.name: str = name
        self._component: str = component
        self._type: str = type
        self.tracked_point: str = tracked_point
        self.units: str = units
        self.placement: str | None = None
        self.reference_frame: str | ReferenceFrame | None = None
        self.description: str | None = None
        self.sampling_frequency: int | float | None = None
        self.status: str | None = None
        self.status_description: str | None = None
        self.columns: MutableSequence[Column] | None = None

        set_attr_from_dict(self, kwargs)

    def __repr__(self) -> str:
        return f"<MotionChannel name={self.name}>"

    @property
    def type(self) -> str | None:
        return self._type

    @type.setter  # noqa: A003
    def type(self, value: str) -> None:
        if value not in MOTION_CHANNEL_TYPE_ALLOWED_FIELD_ENTRIES:
            raise FieldEntryNotValidError(
                f"Field `Type` must be one "
                f"of {MOTION_CHANNEL_TYPE_ALLOWED_FIELD_ENTRIES}"
            )
        self._type = value

    @property
    def component(self) -> str | None:
        return self._component

    @component.setter
    def component(self, value: str) -> None:
        if value not in MOTION_CHANNEL_COMPONENT_ALLOWED_FIELD_ENTRIES:
            raise FieldEntryNotValidError(
                f"Field `Component` must be one "
                f"of {MOTION_CHANNEL_COMPONENT_ALLOWED_FIELD_ENTRIES}"
            )
        self._component = value


class MotionRun(Run):
    def __init__(self, base_path: os.PathLike | str, run_id: int, **kwargs):
        super().__init__(base_path=base_path, run_id=run_id)

        self._channels: MutableSequence[MotionChannel] | None = None
        self._data: Any = None

        set_attr_from_dict(self, kwargs)

    @property
    def acquisition(self) -> "MotionAcquisition | None":
        if self._acquisition:
            return self._acquisition

        warn(
            "Run is not linked to a Acquisition object.", TopLevelEntityNotLinkedWarning
        )
        return self._acquisition

    @acquisition.setter
    def acquisition(self, value: "MotionAcquisition") -> None:
        self._acquisition = value

    @property
    def channels(self) -> MutableSequence[MotionChannel] | None:
        return self._channels

    @channels.setter
    def channels(self, value: MutableSequence[MotionChannel]) -> None:
        self._channels = value

    @property
    def data(self):
        if self._data is None:
            file_name = f"*{self.acquisition.tracking_system.tracking_system_id}*"
            file_name += (
                f"_{self.acquisition.acquisition_id}"
                if len(self.acquisition.tracking_system.acquisitions) > 1
                else ""
            )
            file_name += f"_{self.run_id}" if len(self.acquisition.runs) > 1 else ""
            tsv_path, _ = get_tsv_json_files(
                self.root,
                file_name + "_motion",
            )
            # TODO: put this in a function and write decorator to get files with datalad
            data_frame = load_tsv_data(path=tsv_path, header=None)
            column_names = {}
            for column_number, column in enumerate(self.channels):
                column_names[column_number] = column.name
            data_frame.rename(columns=column_names, inplace=True)

            self._data = data_frame

        return self._data

    @data.setter
    def data(self, value: pd.DataFrame) -> None:
        self._data = value

    def list_channels(self) -> pd.DataFrame:
        channels_dataframe = pd.DataFrame()
        for motion_channel in self.channels if self.channels else []:
            channel_dict = motion_channel.__dict__.copy()
            channel_dict["component"] = channel_dict.pop("_component", None)
            channel_dict["type"] = channel_dict.pop("_type", None)

            channel_dict = delete_none_from_dict(channel_dict)

            reference_frame = channel_dict.pop("reference_frame")
            if isinstance(reference_frame, ReferenceFrame):
                channel_dict["reference_frame"] = reference_frame.name
            else:
                channel_dict["reference_frame"] = reference_frame

            channel_dict.pop("columns")
            # TODO: expand columns
            channels_dataframe = pd.concat(
                [channels_dataframe, pd.DataFrame([channel_dict])],
                ignore_index=True,
            )
        channels_dataframe.dropna(axis=1, how="all", inplace=True)
        return channels_dataframe

    def _reference_frames(self) -> set[ReferenceFrame]:
        reference_frames_set = set()
        for motion_channel in self.channels if self.channels else []:
            reference_frame = motion_channel.reference_frame
            if isinstance(reference_frame, ReferenceFrame):
                reference_frames_set.add(reference_frame)
        return reference_frames_set

    def _columns(self) -> set[Column]:
        columns_set = set()
        for motion_channel in self.channels if self.channels else []:
            for column in motion_channel.columns if motion_channel.columns else []:
                columns_set.add(column)
        return columns_set

    def write(self, output_path: os.PathLike | str) -> None:
        output_path = pathlib.Path(output_path)
        # write motion data to "*_motion.tsv"
        output_path_data = append_path(output_path, "_motion.tsv")
        self.data.to_csv(output_path_data, sep="\t", index=False, header=False)

        # write channels description to "*_channels.tsv"
        output_path_channels = append_path(output_path, "_channels.tsv")
        channels_dataframe = self.list_channels()
        channels_dataframe.to_csv(output_path_channels, sep="\t", index=False)

        # write columns description to "*_channels.json"
        output_path_channel_description = append_path(output_path, "_channels.json")
        channel_description = {}

        columns = self._columns()
        for column in columns:
            column_dict = column.__dict__.copy()
            column_dict.pop("column_name")
            channel_description[column.column_name] = column_dict
        reference_frames = self._reference_frames()

        for reference_frame in reference_frames:
            reference_frame_dict = asdict(reference_frame)
            reference_frame_name = reference_frame_dict.pop("name")
            channel_description["reference_frame"]["Levels"] = {
                reference_frame_name: reference_frame_dict
            }

        channel_description = clean_dict(
            channel_description,
            skip_keys_to_titlecase=1,
        )
        write_json(channel_description, output_path_channel_description)


class MotionAcquisition(BaseAcquisition):
    def __init__(
        self,
        base_path: os.PathLike | str,
        acquisition_id: str,
        sampling_frequency: int | float,
        **kwargs: Any,
    ):
        super().__init__(base_path=base_path, acquisition_id=acquisition_id)

        self.sampling_frequency: int | float = sampling_frequency
        self.accel_channel_count: int | None = None
        self.angaccel_channel_count: int | None = None
        self.gyro_channel_count: int | None = None
        self.jntang_channel_count: int | None = None
        self.latency_channel_count: int | None = None
        self.magn_channel_count: int | None = None
        self.misc_channel_count: int | None = None
        self.missing_values: str | None = None
        self.motion_channel_count: int | None = None
        self.ornt_channel_count: int | None = None
        self.pos_channel_count: int | None = None
        self.sampling_frequency_effective: int | float | None = None
        self.subject_artefact_description: str | None = None
        self.tracked_points_count: int | float | None = None
        self.vel_channel_count: int | None = None

        # Recording duration belongs to run level --> !TODO: move to Run
        self._recording_duration: int | float | None = kwargs.pop(
            "RecordingDuration", None
        )

        # sampling_frequency_effective belongs to run level? --> !TODO: move to Run?
        self._sampling_frequency_effective: int | float | None = kwargs.pop(
            "SamplingFrequencyEffective", None
        )

        self._tracking_system: "TrackSys | None" = None

        set_attr_from_dict(self, kwargs)

    @property
    def tracking_system(self) -> "TrackSys | None":
        if self._tracking_system:
            return self._tracking_system

        warn(
            "Acquisition is not linked to a TrackSys object.",
            TopLevelEntityNotLinkedWarning,
        )
        return self._tracking_system

    @tracking_system.setter
    def tracking_system(self, value: "TrackSys") -> None:
        self._tracking_system = value

    @property
    def runs(self) -> MutableSequence[MotionRun]:
        if not self._runs:
            if self.tracking_system:
                file_name = f"*{self.tracking_system.tracking_system_id}*"
            else:
                file_name = "*"

            tsv_path, json_path = get_tsv_json_files(
                self.root,
                file_name + "_channels",
            )
            channels = get_motion_channels(tsv_path=tsv_path, json_path=json_path)
            self._runs = []
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
                self._runs.append(
                    MotionRun(
                        run_id=run_id_int,
                        base_path=self.root,
                        acquisition=self,
                        channels=channels,
                    )
                )

            # If no runs are found, add a default one
            if not self._runs:
                self._runs.append(
                    MotionRun(
                        run_id=0,
                        base_path=self.root,
                        acquisition=self,
                        channels=channels,
                    )
                )

        return self._runs

    @runs.setter
    def runs(self, value: MutableSequence[int | MotionRun]) -> None:
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, int) for entry in value):
                self._runs = []
                for entry in value:
                    assert isinstance(entry, int)  # for mypy
                    self._runs.append(
                        MotionRun(run_id=entry, base_path=self.root, acquisition=self)
                    )
            elif all(isinstance(v, MotionRun) for v in value):
                self._runs = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Runs` must be a list of Run objects")


class TrackSys(Entity):
    def __init__(
        self,
        base_path: os.PathLike | str,
        tracking_system_id: str,
        motion_description: dict | None = None,
        **kwargs: "dict | Hardware | Institution | MotionTask | MutableSequence",
    ) -> None:
        super().__init__(_entity_id=tracking_system_id, _entity_name="tracksys")
        self._hardware: Hardware | None = None
        self._institution: Institution | None = None
        self._motion_description: dict = (
            motion_description if motion_description else {}
        )

        self.tracking_system_id: str = self._entity_id
        self.tracking_system_name: str | None = self._motion_description.pop(
            "TrackingSystemName", None
        )

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._task: MotionTask | None = None

        self._acquisitions: MutableSequence[MotionAcquisition] | None = None

        set_attr_from_dict(self, kwargs)

    def __repr__(self) -> str:
        return (
            f"<TrackSys id={self.tracking_system_id}, name={self.tracking_system_name}>"
        )

    @property
    def hardware(self) -> Hardware | None:
        return self._hardware

    @hardware.setter
    def hardware(self, value: dict | Hardware) -> None:
        if isinstance(value, dict):
            hardware_data = {}
            for k, v in value.items():
                hardware_data[to_snakecase(k)] = v
            self._hardware = Hardware(**hardware_data)
        elif isinstance(value, Hardware):
            self._hardware = value
        else:
            raise TypeError("Field `Hardware` must be a Hardware object")

    @property
    def institution(self) -> Institution | None:
        return self._institution

    @institution.setter
    def institution(self, value: dict | Institution) -> None:
        if isinstance(value, dict):
            institution_data = {}
            for k, v in value.items():
                institution_data[to_snakecase(k)] = v
            self._institution = Institution(**institution_data)
        elif isinstance(value, Institution):
            self._institution = value
        else:
            raise TypeError("Field `Institution` must be a Institution object")

    @property
    def task(self) -> "MotionTask | None":
        if self._task:
            return self._task

        warn(
            "TrackSys is not linked to a Task object.",
            TopLevelEntityNotLinkedWarning,
        )
        return self._task

    @task.setter
    def task(self, value: "MotionTask") -> None:
        self._task = value

    @property
    def acquisitions(self) -> MutableSequence[MotionAcquisition]:
        if not self._acquisitions:
            self._acquisitions = []
            files = self.root.iterdir()
            acquisition_ids = set()
            for file in files:
                try:
                    acquisition_ids.add(
                        get_entity_from_file(
                            file,
                            "acq",
                        )["acq"]
                    )
                except KeyError:
                    continue
            for acquisition_id in acquisition_ids:
                _, json_path = get_tsv_json_files(
                    self.root,
                    f"*{self.tracking_system_id}_acq-{acquisition_id}_*_motion",
                )

                if json_path:
                    data = parse_motion_json_sidecar(json_path)
                    acquisition_description = data["motion"]
                    sampling_frequency = acquisition_description.pop(
                        "SamplingFrequency"
                    )
                    self._acquisitions.append(
                        MotionAcquisition(
                            base_path=self.root,
                            acquisition_id="acq-" + acquisition_id,
                            tracking_system=self,
                            sampling_frequency=sampling_frequency,
                            **acquisition_description,
                        )
                    )
                elif not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
                    raise NotImplementedError  # TODO: implement

            # If no acquisitions are found, add a default one from
            # the motion description
            if not self._acquisitions:
                self._acquisitions.append(
                    MotionAcquisition(
                        acquisition_id="acq-00",
                        base_path=self.root,
                        tracking_system=self,
                        sampling_frequency=self._motion_description.pop(
                            "SamplingFrequency"
                        ),  # FIXME: dict entry can be None
                        **self._motion_description,
                    )
                )

        return self._acquisitions

    @acquisitions.setter
    def acquisitions(self, value: MutableSequence[Mapping | MotionAcquisition]) -> None:
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, Mapping) for entry in value):
                self._acquisitions = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._acquisitions.append(
                        MotionAcquisition(
                            base_path=self.root, tracking_system=self, **entry
                        )
                    )
            elif all(isinstance(entry, MotionAcquisition) for entry in value):
                self._acquisitions = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError(
                "Field `Acquisitions` must be a list of Acquisition objects"
            )

    def write(self, output_path: os.PathLike | str) -> None:
        write_entities(output_path, self.acquisitions)


class MotionTask(BaseTask):
    def __init__(
        self, base_path: os.PathLike | str, task_name: str, **kwargs: Any
    ) -> None:
        self._tracking_systems: MutableSequence[TrackSys] | None = None

        super().__init__(base_path=base_path, task_name=task_name, **kwargs)

    @property
    def tracking_systems(self) -> MutableSequence[TrackSys]:
        if not self._tracking_systems:
            self._tracking_systems = []
            files = self.root.iterdir()
            tracking_systems_ids = set()
            for file in files:
                try:
                    tracking_systems_ids.add(
                        get_entity_from_file(
                            file,
                            "tracksys",
                        )["tracksys"]
                    )
                except KeyError:
                    continue
            for tracking_system_id in tracking_systems_ids:
                _, json_path = get_tsv_json_files(
                    self.root, f"*tracksys-{tracking_system_id}*_motion"
                )

                if json_path:
                    data = parse_motion_json_sidecar(json_path)
                    motion_description = data["motion"]  # FIXME: can be None
                    hardware_description = data["hardware"]  # FIXME: can be None
                    institution_description = data["institution"]  # FIXME: can be None
                    self._tracking_systems.append(
                        TrackSys(
                            tracking_system_id="tracksys-" + tracking_system_id,
                            base_path=self.root,
                            task=self,
                            hardware=hardware_description,
                            institution=institution_description,
                            motion_description=motion_description,
                        )
                    )
                elif not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
                    raise NotImplementedError  # TODO: implement

            if not self._tracking_systems:
                pass
                # raise ...
                # TODO: If no tracking systems are found raise Error

        return self._tracking_systems

    @tracking_systems.setter
    def tracking_systems(self, value: MutableSequence[Mapping | TrackSys]) -> None:
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, Mapping) for entry in value):
                self._tracking_systems = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._tracking_systems.append(
                        TrackSys(base_path=self.root, task=self, **entry)
                    )
            elif all(isinstance(entry, TrackSys) for entry in value):
                self._tracking_systems = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError(
                "Field `TrackingSystems` must be a list of TrackSys objects"
            )

    def write(self, output_path: os.PathLike | str) -> None:
        # write json sidecar to "*_motion.json"
        task_dict = self.__dict__.copy()
        for tracking_system in self.tracking_systems:
            hardware_dict = (
                asdict(tracking_system.hardware) if tracking_system.hardware else {}
            )
            institution_dict = (
                asdict(tracking_system.institution)
                if tracking_system.institution
                else {}
            )
            output_path_tracksys = append_path(
                output_path, f"_{tracking_system.tracking_system_id}"
            )
            for acquisition in tracking_system.acquisitions:
                acquisition_dict = acquisition.__dict__.copy()
                output_path_acquisition = (
                    append_path(output_path_tracksys, f"_{acquisition.acquisition_id}")
                    if len(tracking_system.acquisitions) > 1
                    else output_path_tracksys
                )
                for run in acquisition.runs:
                    run_dict = run.__dict__.copy()
                    output_path_run = (
                        append_path(output_path_acquisition, f"_{run.run_id}")
                        if len(acquisition.runs) > 1
                        else output_path_acquisition
                    )

                    motion_description = {
                        **task_dict,
                        **hardware_dict,
                        **institution_dict,
                        **acquisition_dict,
                        **run_dict,
                    }
                    motion_description.pop("acquisition_id")
                    motion_description.pop("run_id")
                    motion_description = clean_dict(
                        motion_description, skip_keys_to_titlecase=0
                    )
                    output_path_motion_description = append_path(
                        output_path_run, "_motion.json"
                    )
                    write_json(motion_description, output_path_motion_description)

        write_entities(output_path, self.tracking_systems)


def parse_motion_json_sidecar(sidecar_path: pathlib.Path) -> dict:
    with sidecar_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        task_description = {}
        hardware_description = {}
        institution_description = {}
        motion_description = {}
        for key, value in data.items():
            if re.match(r"^Task[A-Z].*|^Instructions", key):
                task_description[key] = value
            elif re.match(r"^Device[A-Z].*|^Manufacturer.*|^Software[A-Z].*", key):
                hardware_description[key] = value
            elif re.match(r"^Institution.*", key):
                institution_description[key] = value
            else:
                motion_description[key] = value

        return {
            "task": task_description,
            "hardware": hardware_description,
            "institution": institution_description,
            "motion": motion_description,
        }


def get_reference_frames(reference_frames_levels: dict) -> dict[str, ReferenceFrame]:
    reference_frames_dict = {}
    for ref_frame_name, ref_frame_values in reference_frames_levels.items():
        ref_frame_values_snakecase = {}
        for key, val in ref_frame_values.items():
            ref_frame_values_snakecase[to_snakecase(key)] = val
        reference_frames_dict[ref_frame_name] = ReferenceFrame(
            name=ref_frame_name, **ref_frame_values_snakecase
        )

    return reference_frames_dict


def get_motion_channels(
    tsv_path: pathlib.Path | None,
    json_path: pathlib.Path | None,
) -> MutableSequence[MotionChannel]:
    motion_channels: list[MotionChannel] = []
    columns = []
    reference_frames_dict = None

    if json_path:
        column_data = parse_json_sidecar(json_path)

        reference_frames_data = column_data.pop("reference_frame", None)
        if isinstance(reference_frames_data, dict):
            reference_frames_levels = reference_frames_data.pop("Levels")
            reference_frames_dict = get_reference_frames(reference_frames_levels)

        columns.append(Column(name="reference_frame", **reference_frames_data))
        for column_name, column_values in column_data.items():
            columns.append(Column(name=column_name, **column_values))

    if tsv_path:
        data = parse_descriptive_tsv(tsv_path)
        for motion_channel in data:
            assert isinstance(motion_channel, dict), "Must be dicts in Generator."

            reference_frame_name = motion_channel.pop("reference_frame")
            if (
                reference_frames_dict is not None
                and reference_frame_name in reference_frames_dict
            ):
                reference_frame = reference_frames_dict[reference_frame_name]
            else:
                reference_frame = reference_frame_name
            add_object_to_sequence(
                entity_list=motion_channels,
                entity_class=MotionChannel,
                columns=columns,
                reference_frame=reference_frame,
                **motion_channel,
            )

    return motion_channels
