#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause
import os
import pathlib
from dataclasses import dataclass
from typing import Iterable, Mapping

from abidskit.utils.checks import check_if_valid_uri
from abidskit.utils.exceptions import FieldEntryNotValidError, FieldMissingError
from abidskit.utils.helpers import (
    get_entity_from_file,
    set_attr_from_dict,
)
from abidskit.utils.string_manipulation import to_snakecase

FORMAT_ALLOWED_FIELD_ENTRIES = {
    "string",
    "number",
    "integer",
    "boolean",
    "index",
    "label",
    "date",
    "datetime",
    "time",
    "unit",
    "uri",
    "rrid",
    "bids_uri",
    "dataset_relative",
    "file_relative",
    "participant_relative",
    "stimuli_relative",
    "hed_version",
}


@dataclass(slots=True)
class Level:
    level_label: str
    description: str
    term_url: str | None = None

    def __post_init__(self) -> None:
        if self.term_url:
            check_if_valid_uri(self.term_url)

    def __repr__(self) -> str:
        return f"<Level label={self.level_label}>"


class Column:
    def __init__(
        self, column_name: str, **kwargs: str | int | float | Mapping | Iterable
    ) -> None:
        self.column_name: str = column_name

        self.long_name: str | None = None
        self.description: str | None = None
        self._format: str | None = None
        self.units: str | None = None
        self.delimiter: str | None = None
        self.term_url: str | None = None
        self.hed: str | Mapping[str, str] | None = None
        self.maximum: int | float | None = None
        self.minimum: int | float | None = None

        self._levels: Iterable[Level] | None = None

        set_attr_from_dict(self, kwargs)

        if self.term_url:
            check_if_valid_uri(self.term_url)

    def __repr__(self) -> str:
        return f"<Column name={self.column_name} format={self.format}>"

    @property
    def format(self) -> str | None:
        return self._format

    @format.setter
    def format(self, value: str) -> None:
        if value not in FORMAT_ALLOWED_FIELD_ENTRIES:
            raise FieldEntryNotValidError(
                f"Field `Format` must be one of {FORMAT_ALLOWED_FIELD_ENTRIES}"
            )

    @property
    def levels(self) -> Iterable[Level] | None:
        return self._levels

    @levels.setter
    def levels(self, value: Mapping | Iterable[Level]) -> None:
        if isinstance(value, Mapping):
            self._levels = []
            for key, val in value.items():
                if isinstance(val, Mapping):
                    val = {
                        to_snakecase(level_key): level_val
                        for level_key, level_val in val.items()
                    }
                    level = Level(level_label=to_snakecase(key), **val)
                else:
                    level = Level(level_label=to_snakecase(key), description=val)

                self._levels.append(level)
        elif isinstance(value, Iterable) and all(isinstance(v, Level) for v in value):
            self._levels = value
        else:
            raise TypeError("Field `Levels` must be a list of Level objects")


class Acquisition:
    def __init__(self, acquisition_id: str):
        self.acquisition_id: str = acquisition_id

        self.runs = None

    def __repr__(self) -> str:
        return f"<Acquisition id={self.acquisition_id}>"


class Task:
    def __init__(
        self, base_path: os.PathLike | str, task_name: str, **kwargs: str | Iterable
    ) -> None:
        self.task_id: str | None = None
        self.task_name: str = task_name  # !: This is required
        self.task_description: str | None = None
        self.instructions: str | None = None

        # self.cog_atlas_id = None  # !: Only for special datatypes
        # self.cog_poid = None  # !: Only for special datatypes

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._acquisitions: Iterable[Acquisition] | None = None

        if kwargs:
            set_attr_from_dict(self, kwargs)

        if not self.task_name:
            raise FieldMissingError("Field `TaskName` is required in Task")

    def __repr__(self) -> str:
        return f"<Task id={self.task_id}>"

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
