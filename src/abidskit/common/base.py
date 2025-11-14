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
from typing import TYPE_CHECKING, Any, Iterable
from warnings import warn

from abidskit.common.specs_run import Run
from abidskit.utils.exceptions import FieldMissingError, TopLevelEntityNotLinkedWarning
from abidskit.utils.helpers import get_entity_from_file, set_attr_from_dict
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


class BaseAcquisition(ABC):
    @abstractmethod
    def __init__(self, base_path: os.PathLike | str, acquisition_id: str) -> None:
        self.acquisition_id: str = acquisition_id  # !: This is required

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._runs: Iterable[Run] | None = None

    def __repr__(self) -> str:
        return f"<Acquisition id={self.acquisition_id}>"

    @property
    def runs(self) -> Iterable[Run]:
        if not self._runs:
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
                    Run(
                        run_id=run_id,
                        base_path=self.root,
                        acquisition=self,
                    )
                )

            # If no runs are found, add a default one
            if not self._runs:
                self._runs.append(
                    Run(
                        run_id="run-00",
                        base_path=self.root,
                        acquisition=self,
                    )
                )

        return self._runs

    @runs.setter
    def runs(self, value: Iterable[str] | Iterable[Run]) -> None:
        if isinstance(value, Iterable):
            if all(isinstance(entry, str) for entry in value):
                self._runs = []
                for entry in value:
                    assert isinstance(entry, str)  # for mypy
                    self._runs.append(
                        Run(run_id=entry, base_path=self.root, acquisition=self)
                    )
            elif all(isinstance(v, Run) for v in value):
                self._runs = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Runs` must be a list of Run objects")
