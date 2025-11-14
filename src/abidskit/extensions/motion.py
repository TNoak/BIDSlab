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
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Iterable, Mapping
from warnings import warn

from abidskit.common.base import BaseAcquisition, BaseTask
from abidskit.common.specs_misc import Column, Hardware, Institution
from abidskit.common.specs_run import Run
from abidskit.utils.exceptions import TopLevelEntityNotLinkedWarning
from abidskit.utils.helpers import (
    add_entity_to_list,
    get_entity_from_file,
    get_tsv_json_files,
    parse_descriptive_tsv,
    parse_json_sidecar,
    set_attr_from_dict,
)
from abidskit.utils.string_manipulation import to_snakecase


@dataclass(slots=True)
class ReferenceFrame:
    name: str
    rotation_order: str | None = None
    rotation_rule: str | None = None
    spatial_axes: str | None = None
    description: str | None = None

    def __repr__(self) -> str:
        return f"<ReferenceFrame name={self.name}>"


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
        self.component: str = component
        self._type: str = type
        self.tracked_point: str = tracked_point
        self.units: str = units
        self.placement: str | None = None
        self.reference_frame: str | None = None
        self.description: str | None = None
        self.sampling_frequency: int | float | None = None
        self.status: str | None = None
        self.status_description: str | None = None
        self.columns: Iterable[Column] | None = None

        set_attr_from_dict(self, kwargs)

    def __repr__(self) -> str:
        return f"<MotionChannel name={self.name}>"

    @property
    def type(self) -> str:
        return self._type

    @type.setter  # noqa: A003
    def type(self, value: str) -> None:
        self._type = value


class MotionRun(Run):
    def __init__(self, base_path: os.PathLike | str, run_id: str, **kwargs):
        super().__init__(base_path=base_path, run_id=run_id)

        self._channels: Iterable[MotionChannel] | None = None
        self._data: Any = None

        set_attr_from_dict(self, kwargs)

    @property
    def acquisition(self) -> SimpleNamespace | None:
        if self._acquisition:
            acquisition_dict = {
                k.lstrip("_"): v for k, v in vars(self._acquisition).items()
            }
            acquisition_dict.pop("runs")
            return SimpleNamespace(**acquisition_dict)

        assert self._acquisition is None  # for mypy
        warn(
            "Run is not linked to a Acquisition object.", TopLevelEntityNotLinkedWarning
        )
        return self._acquisition

    @acquisition.setter
    def acquisition(self, value: "MotionAcquisition") -> None:
        self._acquisition = value

    @property
    def channels(self) -> Iterable[MotionChannel]:
        return self._channels

    @channels.setter
    def channels(self, value: Iterable[MotionChannel]) -> None:
        self._channels = value

    @property
    def data(self):
        # TODO: implement lazy loading
        return NotImplementedError

    @data.setter
    def data(self, value):
        return NotImplementedError


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
        self.recording_duration: int | float | None = None
        self.subject_artefact_description: str | None = None
        self.tracked_points_count: int | float | None = None
        self.vel_channel_count: int | None = None

        self._tracking_system: "TrackSys | None" = None

        set_attr_from_dict(self, kwargs)

    @property
    def tracking_system(self) -> SimpleNamespace | None:
        if self._tracking_system:
            tracking_system_dict = {
                k.lstrip("_"): v for k, v in vars(self._tracking_system).items()
            }
            tracking_system_dict.pop("acquisitions")
            return SimpleNamespace(**tracking_system_dict)

        assert self._tracking_system is None  # for mypy
        warn(
            "Acquisition is not linked to a TrackSys object.",
            TopLevelEntityNotLinkedWarning,
        )
        return self._tracking_system

    @tracking_system.setter
    def tracking_system(self, value: "TrackSys") -> None:
        self._tracking_system = value

    @property
    def runs(self) -> Iterable[MotionRun]:
        if not self._runs:
            tsv_path, json_path = get_tsv_json_files(
                self.root,
                f"*tracksys-{self.tracking_system.tracking_system_id}*_channels",
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
                self._runs.append(
                    MotionRun(
                        run_id=run_id,
                        base_path=self.root,
                        acquisition=self,
                        channels=channels,
                    )
                )

            # If no runs are found, add a default one
            if not self._runs:
                self._runs.append(
                    MotionRun(
                        run_id="run-00",
                        base_path=self.root,
                        acquisition=self,
                        channels=channels,
                    )
                )

        return self._runs

    @runs.setter
    def runs(self, value: Iterable[str] | Iterable[MotionRun]) -> None:
        if isinstance(value, Iterable):
            if all(isinstance(entry, str) for entry in value):
                self._runs = []
                for entry in value:
                    assert isinstance(entry, str)  # for mypy
                    self._runs.append(
                        MotionRun(run_id=entry, base_path=self.root, acquisition=self)
                    )
            elif all(isinstance(v, MotionRun) for v in value):
                self._runs = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Runs` must be a list of Run objects")


class TrackSys:
    def __init__(
        self,
        base_path: os.PathLike | str,
        tracking_system_id: str,
        **kwargs: "dict | Hardware | Institution | MotionTask | Iterable",
    ) -> None:
        self.tracking_system_id: str = tracking_system_id
        self.tracking_system_name: str | None = kwargs["motion"].pop(
            "TrackingSystemName", None
        )

        self._hardware: Hardware | None = None
        self._institution: Institution | None = None
        self._motion: dict | None = kwargs.pop("motion", None)

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._task: MotionTask | None = None

        self._acquisitions: Iterable[MotionAcquisition] | None = None

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
    def task(self) -> SimpleNamespace | None:
        if self._task:
            task_dict = {k.lstrip("_"): v for k, v in vars(self._task).items()}
            task_dict.pop("tracking_systems")
            return SimpleNamespace(**task_dict)

        assert self._task is None  # for mypy
        warn(
            "TrackSys is not linked to a Task object.",
            TopLevelEntityNotLinkedWarning,
        )
        return self._task

    @task.setter
    def task(self, value: "MotionTask") -> None:
        self._task = value

    @property
    def acquisitions(self) -> Iterable[MotionAcquisition]:
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
                    f"*tracksys-{self.tracking_system_id}_acq-{acquisition_id}_*_motion",
                )

                if json_path:
                    data = parse_motion_json_sidecar(json_path)
                    acquisition_info = data["motion"]
                    sampling_frequency = acquisition_info.pop("SamplingFrequency")
                    self._acquisitions.append(
                        MotionAcquisition(
                            base_path=self.root,
                            acquisition_id="acq-" + acquisition_id,
                            tracking_system=self,
                            sampling_frequency=sampling_frequency,
                            **acquisition_info,
                        )
                    )
                else:
                    raise NotImplementedError  # TODO: implement

            # If no acquisitions are found, add a default one from the motion info
            if not self._acquisitions:
                self._acquisitions.append(
                    MotionAcquisition(
                        acquisition_id="acq-00",
                        base_path=self.root,
                        tracking_system=self,
                        sampling_frequency=self._motion.pop(
                            "SamplingFrequency"
                        ),  # FIXME: can be None
                        **self._motion,
                    )
                )

        return self._acquisitions


class MotionTask(BaseTask):
    def __init__(
        self, base_path: os.PathLike | str, task_name: str, **kwargs: Any
    ) -> None:
        self._tracking_systems = None

        super().__init__(base_path=base_path, task_name=task_name, **kwargs)

    @property
    def tracking_systems(self) -> Iterable[TrackSys]:
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
                    motion_info = data["motion"]  # FIXME: can be None
                    hardware_info = data["hardware"]  # FIXME: can be None
                    institution_info = data["institution"]  # FIXME: can be None
                    self._tracking_systems.append(
                        TrackSys(
                            tracking_system_id=tracking_system_id,
                            base_path=self.root,
                            task=self,
                            hardware=hardware_info,
                            institution=institution_info,
                            motion=motion_info,
                        )
                    )
                else:
                    raise NotImplementedError  # TODO: implement

            # TODO: If no tracking systems are found, add a default one?

        return self._tracking_systems

    @tracking_systems.setter
    def tracking_systems(self, value: Iterable[Mapping] | Iterable[TrackSys]) -> None:
        if isinstance(value, Iterable):
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


def parse_motion_json_sidecar(sidecar_path: pathlib.Path) -> dict:
    with sidecar_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        task_information = {}
        hardware_information = {}
        institution_information = {}
        motion_information = {}
        for key, value in data.items():
            if re.match(r"^Task[A-Z].*|^Instructions", key):
                task_information[key] = value
            elif re.match(r"^Device[A-Z].*|^Manufacturer.*|^Software[A-Z].*", key):
                hardware_information[key] = value
            elif re.match(r"^Institution.*", key):
                institution_information[key] = value
            else:
                motion_information[key] = value

        return {
            "task": task_information,
            "hardware": hardware_information,
            "institution": institution_information,
            "motion": motion_information,
        }


def get_reference_frames(reference_frames_data: dict) -> dict[str, ReferenceFrame]:
    reference_frames_dict = {}
    for ref_frame_name, ref_frame_values in reference_frames_data["Levels"].items():
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
) -> Iterable[MotionChannel]:
    motion_channels: Iterable[MotionChannel] = []
    columns = []
    reference_frames_dict = None

    if json_path:
        column_data = parse_json_sidecar(json_path)

        reference_frames_data = column_data.pop("reference_frame", None)
        if reference_frames_data:
            reference_frames_dict = get_reference_frames(reference_frames_data)

        for column_name, column_values in column_data.items():
            columns.append(Column(column_name=column_name, **column_values))

    if tsv_path:
        data = parse_descriptive_tsv(tsv_path)
        for motion_channel in data:
            assert isinstance(motion_channel, dict)

            reference_frame_name = motion_channel.pop("reference_frame")
            if (
                reference_frames_dict is not None
                and reference_frame_name in reference_frames_dict
            ):
                reference_frame = reference_frames_dict[reference_frame_name]
            else:
                reference_frame = reference_frame_name
            add_entity_to_list(
                entity_list=motion_channels,
                entity_class=MotionChannel,
                columns=columns,
                reference_frame=reference_frame,
                **motion_channel,
            )

    return motion_channels
