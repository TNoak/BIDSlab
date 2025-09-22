#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause
import json
import re

from abidskit.common.specs_misc import Task


class MotionTask(Task):
    def __init__(self, task_name: str, **kwargs):
        self.tracking_system = None

        super().__init__(task_name, **kwargs)


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
