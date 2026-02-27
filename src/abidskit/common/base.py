#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, Sequence
from warnings import warn

from abidskit._typing import R
from abidskit.utils.exceptions import FieldMissingError, TopLevelEntityNotLinkedWarning
from abidskit.utils.helpers import set_attr_from_dict, write_entities
from abidskit.utils.string_manipulation import remove_special_characters

if TYPE_CHECKING:
    from abidskit.common.specs_datatype import Datatype


@dataclass
class Entity(ABC):
    _entity_id: str
    _entity_name: str

    @abstractmethod
    def write(self, output_path: os.PathLike | str) -> None:
        # TODO: implement writing of basic Run data
        raise NotImplementedError


class BaseTask(Entity, ABC):
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

        super().__init__(_entity_id=self.task_id, _entity_name="task")

    def __repr__(self) -> str:
        return f"<Task id={self.task_id}>"

    @abstractmethod
    def write(self, output_path: os.PathLike | str) -> None:
        pass

    @property
    def datatype(self) -> "Datatype | None":
        if self._datatype:
            return self._datatype

        warn("Task is not linked to a Datatype object.", TopLevelEntityNotLinkedWarning)
        return self._datatype

    @datatype.setter
    def datatype(self, value: "Datatype") -> None:
        self._datatype = value


class BaseAcquisition(Entity, Generic[R], ABC):
    @abstractmethod
    def __init__(self, base_path: os.PathLike | str, acquisition_id: str) -> None:
        super().__init__(_entity_id=acquisition_id, _entity_name="acq")
        self.acquisition_id: str = self._entity_id  # !: This is required

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._runs: Sequence[R] | None = None

    def __repr__(self) -> str:
        return f"<Acquisition id={self.acquisition_id}>"

    @property
    @abstractmethod
    def runs(self) -> Sequence[R]:
        pass

    @runs.setter
    @abstractmethod
    def runs(self, value: Sequence[str | R]) -> None:
        pass

    def write(self, output_path: os.PathLike | str) -> None:
        write_entities(output_path, self.runs)
