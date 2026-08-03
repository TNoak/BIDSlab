#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, Sequence
from warnings import warn

import pandas as pd

from abidskit._typing import A, R
from abidskit.utils.exceptions import (
    FieldMissingError,
    FileMissingWarning,
    TopLevelEntityNotLinkedWarning,
)
from abidskit.utils.helpers import (
    append_path,
    check_entity_mismatch,
    load_tsv_data,
    parse_json_sidecar,
    set_attr_from_dict,
    write_entities,
    write_json,
)
from abidskit.utils.string_manipulation import remove_special_characters

if TYPE_CHECKING:
    from abidskit.common.specs_datatype import Datatype


@dataclass
class Entity(ABC):
    _entity_id: str
    _entity_name: str

    @abstractmethod
    def write(self, output_path: os.PathLike | str) -> None: ...

    # recursive method that returns all top level entities above this one
    @abstractmethod
    def get_top_level_entities(self) -> list[str | Any]: ...


class Event(Generic[A]):
    # TODO events files may be in higher directory levels (especially the .json sidecar)
    @abstractmethod
    def __init__(
        self,
        base_path: os.PathLike | str,
        **kwargs: Any,
    ) -> None:
        self.root: pathlib.Path = pathlib.Path(base_path)

        self._run: A | None = None

        self._data: pd.DataFrame | None = None

        self._columns: dict[str, Any] | None = None

        set_attr_from_dict(self, kwargs)

    @property
    def run(self) -> A | None:
        if self._run:
            return self._run

        warn("Event is not linked to a Run object.", TopLevelEntityNotLinkedWarning)
        return self._run

    @run.setter
    def run(self, value: A) -> None:
        self._run = value

    @property
    def columns(self) -> dict[str, Any] | None:
        if self._columns is None and self.run is not None:
            # get list of top level entities
            entities = self.run.get_top_level_entities()

            # get all possible files with _events.json
            files = list(self.root.glob("*_events.json"))
            filenames = [f.name for f in files]
            file_entities = [f.removesuffix("_events.json") for f in filenames]

            # check for entity mismatches and use first one working
            for file in file_entities:
                if check_entity_mismatch(file, entities):
                    # load .json file and save it
                    self._columns = parse_json_sidecar(
                        self.root / (file + "_events.json")
                    )
                    return self._columns

            warn(
                "No matching Events file found.",
                FileMissingWarning,
            )

        return self._columns

    @columns.setter
    def columns(self, value: dict[str, Any]) -> None:
        self._columns = value

    @property
    def data(self) -> pd.DataFrame | None:
        if self._data is None and self.run is not None:
            # get list of top level entities
            entities = self.run.get_top_level_entities()

            # get all possible files with _events.tsv
            files = list(self.root.glob("*_events.tsv"))
            filenames = [f.name for f in files]
            file_entities = [f.removesuffix("_events.tsv") for f in filenames]

            # check for entity mismatches and use first one working
            for file in file_entities:
                if check_entity_mismatch(file, entities):
                    # load .tsv file and save a dataframe
                    self._data = load_tsv_data(path=self.root / (file + "_events.tsv"))
                    return self._data

            warn(
                "No matching Events file found.",
                FileMissingWarning,
            )

        return self._data

    @data.setter
    def data(self, value: pd.DataFrame) -> None:
        self._data = value

    def write(self, output_path: os.PathLike | str) -> None:
        output_path_json = append_path(output_path, "_events.json")
        output_path_tsv = append_path(output_path, "_events.tsv")

        if self.columns is not None:
            write_json(content=self.columns, output_path=output_path_json)
        if self.data is not None:
            self.data.to_csv(output_path_tsv, sep="\t", index=False, header=False)


class Run(Entity, Generic[A]):
    def __init__(self, base_path: os.PathLike | str, run_id: str, **kwargs: Any):
        super().__init__(_entity_id=run_id, _entity_name="run")
        self.run_id = self._entity_id
        # make sure that run_id is "run-<int>"
        assert re.match(r"run-[0-9]+", self.run_id), (
            "run_id does not follow the pattern run-<int>"
        )

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._acquisition: A | None = None

        self._recordings = None
        self._events: Sequence[dict] | Sequence[Event] | None = None

        set_attr_from_dict(self, kwargs)

    def __repr__(self):
        return f"Run id={self.run_id}"

    @property
    def acquisition(self) -> A | None:
        if self._acquisition:
            return self._acquisition

        warn(
            "Run is not linked to a Acquisition object.", TopLevelEntityNotLinkedWarning
        )
        return self._acquisition

    @acquisition.setter
    def acquisition(self, value: A) -> None:
        self._acquisition = value

    # @property
    # def recordings(self):
    #    raise NotImplementedError

    # @recordings.setter
    # def recordings(self, value: Sequence[dict] | Sequence[Recording]):
    #    raise NotImplementedError

    @property
    def events(self):
        if self._events is None:
            self._events = []
            self._events.append(Event(base_path=self.root, run=self))
        return self._events

    @events.setter
    def events(self, value: Sequence[dict] | Sequence[Event]) -> None:
        self._events = value

    def get_top_level_entities(self) -> list[str | Any]:
        assert self.acquisition is not None
        entities = self.acquisition.get_top_level_entities()
        entities.append(self._entity_id)
        return entities

    def write(self, output_path: os.PathLike | str) -> None:
        event = self.events
        if event is not None:
            [e.write(output_path) for e in event]


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

    def get_top_level_entities(self) -> list[str | Any]:
        assert self.datatype is not None
        entities = self.datatype.get_top_level_entities()
        entities.append(self.task_id)
        return entities

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

        self._runs: dict[str, R] | None = None

    def __repr__(self) -> str:
        return f"<Acquisition id={self.acquisition_id}>"

    @property
    @abstractmethod
    def runs(self) -> dict[str, R]:
        pass

    @runs.setter
    @abstractmethod
    def runs(self, value: Sequence[str | R] | dict[str, R]) -> None:
        pass

    def write(self, output_path: os.PathLike | str) -> None:
        write_entities(output_path, self.runs.values())
