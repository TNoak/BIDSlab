#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from warnings import warn

from abidskit.utils.exceptions import TopLevelEntityNotLinkedWarning
from abidskit.utils.helpers import set_attr_from_dict

if TYPE_CHECKING:
    from abidskit.common.specs_misc import Acquisition


class Run:
    def __init__(self, base_path: os.PathLike | str, run_id: str, **kwargs: Any):
        self.run_id = run_id
        # TODO: make sure that run_id is "run-<int>"

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._acquisition = None

        self._recordings = None
        self._events = None

        set_attr_from_dict(self, kwargs)

    def __repr__(self):
        return f"Run id={self.run_id}"

    @property
    def acquisition(self) -> SimpleNamespace | None:
        if self._acquisition:
            acquisition_dict = {
                k.lstrip("_"): v for k, v in vars(self._acquisition).items()
            }
            acquisition_dict.pop("tasks")
            return SimpleNamespace(**acquisition_dict)

        assert self._acquisition is None  # for mypy
        warn(
            "Run is not linked to a Acquisition object.", TopLevelEntityNotLinkedWarning
        )
        return self._acquisition

    @acquisition.setter
    def acquisition(self, value: "Acquisition") -> None:
        self._acquisition = value

    # @property
    # def recordings(self):
    #     raise NotImplementedError

    # @recordings.setter
    # def recordings(self, value: Iterable[dict] | Iterable[Recording]):
    #     raise NotImplementedError

    # @property
    # def events(self):
    #     raise NotImplementedError

    # @events.setter
    # def events(self, value: Iterable[dict] | Iterable[Event]):
    #     raise NotImplementedError
