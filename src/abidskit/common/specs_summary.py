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
from typing import TYPE_CHECKING, Any, Iterable, Mapping
from warnings import warn

from abidskit.common.specs_datatype import Datatype
from abidskit.common.specs_misc import Column
from abidskit.utils.exceptions import FieldMissingError, TopLevelEntityNotLinkedWarning
from abidskit.utils.helpers import (
    get_matching_subpaths,
    get_tsv_json_files,
    parse_descriptive_tsv,
    parse_json_sidecar,
)

if TYPE_CHECKING:
    from abidskit.common.specs_description import Dataset

ALLOWED_DATATYPES = {
    "func",
    "dwi",
    "fmap",
    "anat",
    "perf",
    "meg",
    "eeg",
    "ieeg",
    "beh",
    "pet",
    "micr",
    "nirs",
    "motion",
    "mrs",
}


class Scan:
    def __init__(
        self, base_path: os.PathLike | str, filename: os.PathLike | str, **kwargs: Any
    ) -> None:
        self.filename: pathlib.Path = pathlib.Path(filename)
        self.acq_time: str | None = None
        self.hed: str | None = None
        self.columns: Iterable[str] | None = None

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._session: Session | None = None

        for key, value in kwargs.items():
            setattr(self, key, value)

        if not filename:
            raise FieldMissingError("Field `Filename` is required in Scan")

    def __repr__(self) -> str:
        return f"<Scan filename={self.filename}>"

    @property
    def filepath(self) -> pathlib.Path:
        return self.root / self.filename

    @property
    def session(self) -> SimpleNamespace | None:
        if self._session:
            session_dict = {k.lstrip("_"): v for k, v in vars(self._session).items()}
            session_dict.pop("scans")
            return SimpleNamespace(**session_dict)

        assert self._session is None  # for mypy
        warn("Scan is not linked to a Session object.", TopLevelEntityNotLinkedWarning)
        return self._session

    @session.setter
    def session(self, value: "Session") -> None:
        self._session = value


class Session:
    def __init__(
        self, base_path: os.PathLike | str, session_id: str, **kwargs: Any
    ) -> None:
        self.session_id: str = session_id  # !: This is required
        self.acq_time: str | None = None
        self.pathology: str | int | None = None  # TODO: check if same as in samples
        self.hed: str | None = None

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._participant: Participant | None = None

        self._scans: Iterable[Scan] | None = None
        self._datatypes: Iterable[Datatype] | None = None

        for key, value in kwargs.items():
            setattr(self, key, value)

        if not session_id:
            raise FieldMissingError("Field `Session_id` is required in Session")

    def __repr__(self) -> str:
        return f"<Session id={self.session_id}>"

    @property
    def participant(self) -> SimpleNamespace | None:
        if self._participant:
            participant_dict = {
                k.lstrip("_"): v for k, v in vars(self._participant).items()
            }
            participant_dict.pop("sessions")
            return SimpleNamespace(**participant_dict)

        assert self._participant is None  # for mypy
        warn(
            "Session is not linked to a Participant object.",
            TopLevelEntityNotLinkedWarning,
        )
        return self._participant

    @participant.setter
    def participant(self, value: "Participant") -> None:
        self._participant = value

    @property
    def scans(self) -> Iterable[Scan] | None:
        if not self._scans:
            # For every level before sessions
            # scans.json can be in root, subject or session level
            # scans.tsv can be in subject or session level
            column_data = {}

            # if no top-level entities are linked
            try:
                if participant := self.participant:
                    dataset_root = participant.dataset.root
            except AttributeError:
                dataset_root = self.root

            for dir_level in get_matching_subpaths(
                path=self.root,
                matches=["sub-*", "ses-*"],
                root=dataset_root,
            ) + [dataset_root]:
                tsv_path, json_path = get_tsv_json_files(dir_level, "*scans")
                columns = []

                if json_path:
                    column_data.update(parse_json_sidecar(json_path))

                if column_data:
                    for column_name, column_values in column_data.items():
                        columns.append(Column(column_name=column_name, **column_values))

                if tsv_path and dir_level != self.root.parent.parent:
                    self._scans = []
                    data = parse_descriptive_tsv(tsv_path)
                    for scan in data:
                        self._scans.append(
                            Scan(
                                base_path=self.root,
                                **scan,
                                columns=columns,
                                session=self,
                            )
                        )

        # TODO: implement automatic scan detection
        return self._scans

    @scans.setter
    def scans(self, value: Iterable[Mapping] | Iterable[Scan]) -> None:
        # TODO: handle columns here
        if isinstance(value, Iterable):
            if all(isinstance(entry, Mapping) for entry in value):
                self._scans = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._scans.append(Scan(base_path=self.root, session=self, **entry))
            elif all(isinstance(entry, Scan) for entry in value):
                self._scans = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Scans` must be a list of Scan objects")

    @property
    def datatypes(self) -> Iterable[Datatype]:
        if not self._datatypes:
            self._datatypes = []
            for file in self.root.iterdir():
                if file.is_dir() and file.name in ALLOWED_DATATYPES:
                    self._datatypes.append(
                        Datatype(base_path=file, datatype_name=file.name, session=self)
                    )

        return self._datatypes

    @datatypes.setter
    def datatypes(self, value: Iterable[str] | Iterable[Datatype]) -> None:
        if isinstance(value, Iterable):
            if all(isinstance(entry, str) for entry in value):
                self._datatypes = []
                for entry in value:
                    assert isinstance(entry, str)  # for mypy
                    if entry in ALLOWED_DATATYPES:
                        self._datatypes.append(
                            Datatype(
                                base_path=self.root / entry,
                                datatype_name=entry,
                                session=self,
                            )
                        )
            elif all(isinstance(entry, Datatype) for entry in value):
                self._datatypes = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Datatypes` must be a list of Datatype objects")


class Participant:
    def __init__(
        self,
        base_path: os.PathLike | str,
        participant_id: str,
        **kwargs: Any,
    ) -> None:
        self.participant_id: str = participant_id  # !: This is required
        self.species: str | int | None = "homo sapiens"
        self.age: int | None = None
        self.sex: str | None = None
        self.handedness: str | None = None
        self.strain: str | int | None = None
        self.strain_rrid: str | None = None
        self.hed: str | None = None

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._dataset: Dataset | None = None

        self.columns: Iterable[Column] | None = None

        self._sessions: Iterable[Session] | None = None

        for key, value in kwargs.items():
            setattr(self, key, value)

        if not participant_id:
            raise FieldMissingError("Field `Participant_id` is required in Participant")

    def __repr__(self) -> str:
        return f"<Participant id={self.participant_id}>"

    @property
    def dataset(self) -> SimpleNamespace | None:
        if self._dataset:
            dataset_dict = {k.lstrip("_"): v for k, v in vars(self._dataset).items()}
            dataset_dict.pop("participants")
            return SimpleNamespace(**dataset_dict)

        assert self._dataset is None  # for mypy
        warn("Participant is not linked to a Dataset", TopLevelEntityNotLinkedWarning)
        return self._dataset

    @dataset.setter
    def dataset(self, value: "Dataset") -> None:
        self._dataset = value

    @property
    def sessions(self) -> Iterable[Session]:
        if not self._sessions:
            tsv_path, _ = get_tsv_json_files(
                self.root, f"{self.participant_id}_sessions"
            )
            self._sessions = []
            if tsv_path:
                data = parse_descriptive_tsv(tsv_path)
                for session in data:
                    self._sessions.append(
                        Session(
                            base_path=self.root / session.get("session_id"),
                            participant=self,
                            **session,
                        )
                    )
            else:
                dirs = self.root.iterdir()
                for directory in dirs:
                    if directory.is_dir() and directory.name.startswith("ses-"):
                        self._sessions.append(
                            Session(
                                base_path=self.root / directory.name,
                                session_id=directory.name,
                                participant=self,
                            )
                        )

            # If no sessions are found, create a default one
            if not self._sessions:
                self._sessions.append(
                    Session(
                        base_path=self.root,
                        session_id="ses-00",
                        participant=self,
                    )
                )

        return self._sessions

    @sessions.setter
    def sessions(self, value: Iterable[Mapping] | Iterable[Session]) -> None:
        if isinstance(value, Iterable):
            if all(isinstance(entry, Mapping) for entry in value):
                self._sessions = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._sessions.append(Session(base_path=self.root, **entry))
            elif all(isinstance(entry, Session) for entry in value):
                self._sessions = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Sessions` must be a list of Session objects")
