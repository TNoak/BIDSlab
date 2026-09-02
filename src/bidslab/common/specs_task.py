#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
from typing import TYPE_CHECKING, MutableSequence

from bidslab.common.base import BaseTask
from bidslab.common.specs_misc import Acquisition
from bidslab.settings import get_settings_value
from bidslab.utils.helpers import get_entity_from_file

if TYPE_CHECKING:
    from bidslab.common.specs_datatype import Datatype


class Task(BaseTask):
    def __init__(
        self,
        base_path: os.PathLike | str,
        task_name: str,
        **kwargs: "str | Datatype | MutableSequence",
    ) -> None:
        self.cog_atlas_id = None  # !: Only for special datatypes
        self.cog_poid = None  # !: Only for special datatypes

        self._acquisitions: dict[str, Acquisition] | None = None

        super().__init__(base_path=base_path, task_name=task_name, **kwargs)

    @property
    def acquisitions(self) -> dict[str, Acquisition]:
        if not self._acquisitions:
            self._acquisitions = {}
            files = self.root.iterdir()
            acquisition_labels = set()
            for file in files:
                try:
                    acquisition_labels.add(
                        get_entity_from_file(
                            file,
                            "acq",
                        )["acq"]
                    )
                except KeyError:
                    continue
            for acquisition_label in acquisition_labels:
                self._acquisitions.update(
                    {
                        "acq-" + acquisition_label: Acquisition(
                            acquisition_id="acq-" + acquisition_label,
                            base_path=self.root,
                        )
                    }
                )

            # If no acquisitions are found, add a default one
            if not self._acquisitions:
                self._acquisitions.update(
                    {
                        "acq-00": Acquisition(
                            acquisition_id="acq-00",
                            base_path=self.root,
                            virtual_entity=True,
                        )
                    }
                )

        return self._acquisitions

    @acquisitions.setter
    def acquisitions(
        self, value: MutableSequence[str | Acquisition] | dict[str, Acquisition]
    ) -> None:
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, str) for entry in value):
                self._acquisitions = {}
                for entry in value:
                    assert isinstance(entry, str)  # for mypy
                    self._acquisitions.update(
                        {
                            entry: Acquisition(
                                acquisition_id=entry,
                                base_path=self.root,
                            )
                        }
                    )
            elif all(isinstance(v, Acquisition) for v in value):
                self._acquisitions = {}
                for entry in value:
                    assert isinstance(entry, Acquisition)  # for mypy
                    self._acquisitions.update({entry.acquisition_id: entry})
        elif isinstance(value, dict):
            self._acquisitions = value
        else:
            raise TypeError(
                "Field `Acquisitions` must be a list of Acquisition objects"
            )

    def write(self, output_path: os.PathLike | str) -> None:
        # TODO: implement writing of basic Task data
        if not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
            raise NotImplementedError
