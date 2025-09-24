#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib
from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from warnings import warn

from abidskit.utils.exceptions import FieldMissingError, TopLevelEntityNotLinkedWarning
from abidskit.utils.helpers import set_attr_from_dict
from abidskit.utils.string_manipulation import remove_special_characters

if TYPE_CHECKING:
    from abidskit.common.specs_datatype import Datatype


class BaseTask(ABC):
    @abstractmethod
    def __init__(
        self,
        base_path: os.PathLike | str,
        task_name: str,
        **kwargs: Any,
    ) -> None:
        self.task_id: str | None = None
        self.task_name: str = task_name  # !: This is required
        self.task_description: str | None = None
        self.instructions: str | None = None

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._datatype: Datatype | None = None

        if kwargs:
            set_attr_from_dict(self, kwargs)

        if not self.task_name:
            raise FieldMissingError("Field `TaskName` is required in Task")

        if not self.task_id:
            self.task_id = f"task-{remove_special_characters(self.task_name)}"

    def __repr__(self) -> str:
        return f"<Task id={self.task_id}>"

    @property
    def datatype(self) -> SimpleNamespace | None:
        if self._datatype:
            datatype_dict = {k.lstrip("_"): v for k, v in vars(self._datatype).items()}
            datatype_dict.pop("tasks")
            return SimpleNamespace(**datatype_dict)

        assert self._datatype is None  # for mypy
        warn("Task is not linked to a Datatype object.", TopLevelEntityNotLinkedWarning)
        return self._datatype

    @datatype.setter
    def datatype(self, value: "Datatype") -> None:
        self._datatype = value
