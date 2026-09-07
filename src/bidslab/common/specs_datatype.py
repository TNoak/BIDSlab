#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib
from typing import TYPE_CHECKING, Any, Iterable, Mapping
from warnings import warn

from bidslab.common.base import BaseTask
from bidslab.common.specs_task import Task
from bidslab.extensions.emg import EMGTask, parse_emg_json_sidecar
from bidslab.extensions.motion import MotionTask, parse_motion_json_sidecar
from bidslab.settings import get_settings_value
from bidslab.utils.dict_manipulation import ManipulateKeysOption, clean_dict
from bidslab.utils.exceptions import TopLevelEntityNotLinkedWarning
from bidslab.utils.helpers import (
    get_entity_from_file,
    get_tsv_json_files,
    set_attr_from_dict,
    write_entities,
)
from bidslab.utils.string_manipulation import to_snakecase

if TYPE_CHECKING:
    from bidslab.common.specs_summary import Session

DATATYPES_WITH_TASKS = {
    # "anat",  # needs special implementation
    "meg",
    "eeg",
    "ieeg",
    "beh",
    "pet",
    "nirs",
    "motion",
    "emg",
}


class Datatype:
    def __init__(
        self,
        base_path: os.PathLike | str,
        datatype_name: str,
        **kwargs: "Session | Iterable",
    ) -> None:
        self.datatype_name: str = datatype_name

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._session: Session | None = None

        self._tasks: dict[str, BaseTask] | None = None

        if kwargs:
            set_attr_from_dict(self, kwargs)

    def __repr__(self) -> str:
        return f"<Datatype datatype_name={self.datatype_name}>"

    @property
    def session(self) -> "Session | None":
        if self._session:
            return self._session

        warn(
            "Datatype is not linked to a Session object.",
            TopLevelEntityNotLinkedWarning,
        )
        return self._session

    @session.setter
    def session(self, value: "Session") -> None:
        self._session = value

    @property
    def tasks(self) -> dict[str, BaseTask]:
        if not self._tasks:
            self._tasks = {}
            if self.datatype_name in DATATYPES_WITH_TASKS:
                files = self.root.iterdir()
                task_ids = set()
                for file in files:
                    try:
                        task_ids.add(
                            get_entity_from_file(
                                file,
                                "task",
                            )["task"]
                        )
                    except KeyError:
                        continue
                for task_id in task_ids:
                    _, json_path = get_tsv_json_files(
                        self.root, f"*task-{task_id}*_{self.datatype_name}"
                    )

                    if json_path:
                        if self.datatype_name == "motion":
                            data = parse_motion_json_sidecar(json_path)
                            task_name = data["task"].pop("TaskName")
                            self._tasks.update(
                                {
                                    "task-" + task_id: MotionTask(
                                        task_id="task-" + task_id,
                                        task_name=task_name,
                                        base_path=self.root,
                                        datatype=self,
                                        **data["task"],
                                    )
                                }
                            )
                        elif self.datatype_name == "emg":
                            data = parse_emg_json_sidecar(json_path)
                            data_desc = clean_dict(
                                data,
                                skip_keys_to_manipulate=ManipulateKeysOption.ALL_KEYS_MANIPULATE,
                                string_manipulation=to_snakecase,
                            )
                            # TODO: add electrodes here
                            task_description = data_desc.pop("task", None)
                            task_name = task_description.pop("task_name", None)
                            description = {
                                "_description": data_desc,
                                **task_description,
                            }
                            self._tasks.update(
                                {
                                    "task-" + task_id: EMGTask(
                                        task_id="task-" + task_id,
                                        task_name=task_name,
                                        base_path=self.root,
                                        datatype=self,
                                        **description,
                                    )
                                }
                            )
                        elif not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
                            raise NotImplementedError

                    elif not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
                        raise NotImplementedError

            elif not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
                raise NotImplementedError

            # If no tasks are found, create a default one
            if not self._tasks:
                self._tasks.update(
                    {
                        "task-00": Task(
                            task_name="n/a",
                            task_id="task-00",
                            base_path=self.root,
                            virtual_entity=True,
                            datatype=self,
                        )
                    }
                )

        return self._tasks

    @tasks.setter
    def tasks(self, value: Iterable[Mapping] | Iterable[BaseTask]) -> None:
        if isinstance(value, Iterable):
            if all(isinstance(entry, Mapping) for entry in value):
                self._tasks = {}
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._tasks.update(
                        {entry.task_id: Task(base_path=self.root, **entry)}  # type: ignore[attr-defined]
                    )
            elif all(isinstance(entry, BaseTask) for entry in value):
                self._tasks = {}
                for entry in value:
                    assert isinstance(entry, BaseTask)  # for mypy
                    assert entry.task_id is not None
                    self._tasks.update({entry.task_id: entry})
        else:
            raise TypeError("Field `Tasks` must be a list of Task objects")

    def get_top_level_entities(self) -> list[str | Any]:
        assert self.session is not None
        return self.session.get_top_level_entities()

    def write(self, output_path: os.PathLike | str) -> None:
        write_entities(output_path, self.tasks.values())
