#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import json
import os
import re
from typing import Any, Iterable, Mapping

from abidskit.common.base import BaseTask
from abidskit.common.specs_misc import Hardware, Institution
from abidskit.utils.helpers import (
    get_entity_from_file,
    get_tsv_json_files,
    set_attr_from_dict,
)
from abidskit.utils.string_manipulation import to_snakecase


class TrackSys:
    def __init__(self, base_path, tracking_system_id, **kwargs):
        self.tracking_system_id = tracking_system_id
        self.tracking_system_name = None

        self._hardware = None
        self._institution = None
        self.motion = None

        self.root = base_path

        self._task = None

        self._acquisitions = None

        set_attr_from_dict(self, kwargs)

    def __repr__(self):
        return f"TrackSys(tracking_system_id={self.tracking_system_id}, tracking_system_name={self.tracking_system_name})"

    @property
    def hardware(self):
        return self._hardware

    @hardware.setter
    def hardware(self, value: dict | Hardware):
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
    def institution(self):
        return self._institution

    @institution.setter
    def institution(self, value: dict | Institution):
        if isinstance(value, dict):
            institution_data = {}
            for k, v in value.items():
                institution_data[to_snakecase(k)] = v
            self._institution = Institution(**institution_data)
        elif isinstance(value, Institution):
            self._institution = value
        else:
            raise TypeError("Field `Institution` must be a Institution object")


class MotionTask(BaseTask):
    def __init__(
        self, base_path: os.PathLike | str, task_name: str, **kwargs: Any
    ) -> None:
        self._tracking_systems = None

        super().__init__(base_path=base_path, task_name=task_name, **kwargs)

    @property
    def tracking_systems(self):
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
                    tracking_system = data["motion"]
                    hardware = data["hardware"]
                    institution = data["institution"]
                    self._tracking_systems.append(
                        TrackSys(
                            tracking_system_id=tracking_system_id,
                            base_path=self.root,
                            hardware=hardware,
                            institution=institution,
                            motion=tracking_system,
                        )
                    )
                else:
                    raise NotImplementedError  # TODO: implement

        return self._tracking_systems

    @tracking_systems.setter
    def tracking_systems(self, value: Iterable[Mapping] | Iterable[TrackSys]) -> None:
        if isinstance(value, Iterable):
            if all(isinstance(entry, Mapping) for entry in value):
                self._tracking_systems = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._tracking_systems.append(
                        TrackSys(base_path=self.root, **entry)
                    )
            elif all(isinstance(entry, TrackSys) for entry in value):
                self._tracking_systems = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError(
                "Field `TrackingSystems` must be a list of TrackSys objects"
            )


def parse_motion_json_sidecar(sidecar_path):
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
