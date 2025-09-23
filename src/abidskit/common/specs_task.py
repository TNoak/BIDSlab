#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib
from _warnings import warn
from types import SimpleNamespace
from typing import TYPE_CHECKING, Iterable

from abidskit.common.specs_misc import Acquisition
from abidskit.utils.exceptions import FieldMissingError, TopLevelEntityNotLinkedWarning
from abidskit.utils.helpers import get_entity_from_file, set_attr_from_dict

if TYPE_CHECKING:
    from abidskit.common.specs_datatype import Datatype


class Task:
    def __init__(
        self,
        base_path: os.PathLike | str,
        task_name: str,
        **kwargs: "str | Datatype | Iterable",
    ) -> None:
        self.task_id: str | None = None
        self.task_name: str = task_name  # !: This is required
        self.task_description: str | None = None
        self.instructions: str | None = None

        self.cog_atlas_id = None  # !: Only for special datatypes
        self.cog_poid = None  # !: Only for special datatypes

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._datatype: Datatype | None = None

        self._acquisitions: Iterable[Acquisition] | None = None

        if kwargs:
            set_attr_from_dict(self, kwargs)

        if not self.task_name:
            raise FieldMissingError("Field `TaskName` is required in Task")

        # TODO: Implement building of task_id from task_name
        # if not self.task_id:

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

    @property
    def acquisitions(self) -> Iterable[Acquisition]:
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
                self._acquisitions.append(Acquisition(acquisition_id=acquisition_id))

            # If no acquisitions are found, add a default one
            if not self._acquisitions:
                self._acquisitions.append(Acquisition(acquisition_id="acq-00"))

        return self._acquisitions

    @acquisitions.setter
    def acquisitions(self, value: Iterable[str] | Iterable[Acquisition]) -> None:
        if isinstance(value, Iterable):
            if all(isinstance(entry, str) for entry in value):
                self._acquisitions = []
                for entry in value:
                    assert isinstance(entry, str)  # for mypy
                    self._acquisitions.append(Acquisition(acquisition_id=entry))
            elif all(isinstance(v, Acquisition) for v in value):
                self._acquisitions = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError(
                "Field `Acquisitions` must be a list of Acquisition objects"
            )
