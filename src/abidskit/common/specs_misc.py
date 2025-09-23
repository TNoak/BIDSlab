#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Mapping

from abidskit.utils.checks import check_if_valid_uri
from abidskit.utils.exceptions import (
    FieldEntryNotValidError,
)
from abidskit.utils.helpers import (
    set_attr_from_dict,
)
from abidskit.utils.string_manipulation import to_snakecase

if TYPE_CHECKING:
    from abidskit.common.specs_task import Task

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

        self._task: Task | None = None

        self._runs: Iterable[Run] | None = None

    def __repr__(self) -> str:
        return f"<Acquisition id={self.acquisition_id}>"

    @property
    def task(self) -> "Task | None":
        raise NotImplementedError

    @task.setter
    def task(self, value: "Task") -> None:
        raise NotImplementedError

    # @property
    # def runs(self) -> Iterable[Run]:
    #     raise NotImplementedError
    #
    # @runs.setter
    # def runs(self, value: Iterable[dict] | Iterable[Run]) -> None:
    #     raise NotImplementedError
