#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib
from types import SimpleNamespace
from typing import TYPE_CHECKING, Iterable, Mapping

from abidskit.common.specs_misc import Task
from abidskit.utils.helpers import (
    get_entity_from_file,
    get_tsv_json_files,
)

if TYPE_CHECKING:
    from abidskit.common.specs_summary import Session

DATATYPES_WITH_TASKS = {
    # "anat",  # needs special implementation
    "meg",
    "eeg",
    "ieeg",
    "beh",
    "pet",
    "nirs",
    "motion",
}


class Datatype:
    def __init__(
        self,
        base_path: os.PathLike | str,
        datatype_name: str,
        session: "Session",
        # **kwargs: Any,
    ) -> None:
        self.datatype_name: str = datatype_name

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._session: Session | None = None
        self.session = session

        self._tasks: Iterable[Task] | None = None

        # if kwargs:
        #     set_attr_from_dict(self, kwargs)

    def __repr__(self) -> str:
        return f"<Datatype datatype_name={self.datatype_name}>"

    @property
    def session(self) -> SimpleNamespace:
        session_dict = {k.lstrip("_"): v for k, v in vars(self._session).items()}
        session_dict.pop("datatypes")
        return SimpleNamespace(**session_dict)

    @session.setter
    def session(self, value: "Session") -> None:
        self._session = value

    @property
    def tasks(self) -> Iterable[Task]:
        if not self._tasks:
            self._tasks = []
            if self.datatype_name in DATATYPES_WITH_TASKS:
                files = self.root.iterdir()
                task_names = []
                for file in files:
                    task_names.append(
                        get_entity_from_file(
                            file,
                            "task",
                        )["task"]
                    )
                for task_name in task_names:
                    _, json_path = get_tsv_json_files(
                        self.root, f"*task-{task_name}*_{self.datatype_name}"
                    )

        return self._tasks

    @tasks.setter
    def tasks(self, value: Iterable[Mapping] | Iterable[Task]) -> None:
        if isinstance(value, Iterable):
            if all(isinstance(entry, Mapping) for entry in value):
                self._tasks = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._tasks.append(Task(**entry))
            elif all(isinstance(entry, Task) for entry in value):
                self._tasks = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Tasks` must be a list of Task objects")
