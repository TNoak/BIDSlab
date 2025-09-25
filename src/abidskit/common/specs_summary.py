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
from typing import TYPE_CHECKING, Any, Iterable, List, Mapping
from warnings import warn

from abidskit.common.specs_datatype import Datatype
from abidskit.common.specs_misc import Column
from abidskit.utils.exceptions import FieldMissingError, TopLevelEntityNotLinkedWarning
from abidskit.utils.helpers import (
    add_entity_to_list,
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
            # if no top-level entities are linked
            # try-except necessary since participant and dataset might not be linked
            # and thus participant would be None or accessing participant.dataset would
            # raise an AttributeError
            # TODO: test this
            try:
                if participant := self.participant:
                    dataset_root = participant.dataset.root
            except AttributeError:
                dataset_root = self.root

            self._scans = get_scans_from_files(self, dataset_root=dataset_root)

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
            self._sessions = get_sessions_from_files(self, tsv_path=tsv_path)

            # If no sessions are found, create a default one
            if len(self._sessions) == 0:
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


def get_sessions_from_files(
    participant: Participant,
    tsv_path: pathlib.Path | None,
) -> List[Session]:
    sessions: List[Session] = []
    if tsv_path:
        data = parse_descriptive_tsv(tsv_path)
        for session in data:
            assert isinstance(session, dict)
            session_id = session.get("session_id")
            if session_id is None:
                raise FieldMissingError(
                    "Field `session_id` is required as column in sessions.tsv"
                )
            add_entity_to_list(
                entity_list=sessions,
                entity_class=Session,
                base_path=participant.root / session_id,
                participant=participant,
                **session,
            )
    else:
        dirs = participant.root.iterdir()
        for directory in dirs:
            if directory.is_dir() and directory.name.startswith("ses-"):
                add_entity_to_list(
                    entity_list=sessions,
                    entity_class=Session,
                    base_path=participant.root / directory.name,
                    session_id=directory.name,
                    participant=participant,
                )

    return sessions


def get_scans_from_files(
    session: Session,
    dataset_root: pathlib.Path,
) -> List[Scan]:
    # For every level before sessions:
    # - scans.json can be in root, subject or session level
    # - scans.tsv can be in subject or session level and the one from the entity
    #   furthest down the hierarchy is used
    # TODO: make sure that the order of dir_levels is correct, such that dataset_root
    #  is first and session last
    column_data = {}
    scans: List[Scan] = []

    for dir_level in get_matching_subpaths(
        path=session.root,
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

        if tsv_path and dir_level != dataset_root:
            scans = []
            data = parse_descriptive_tsv(tsv_path)
            for scan in data:
                add_entity_to_list(
                    entity_list=scans,
                    entity_class=Scan,
                    base_path=session.root,
                    session=session,
                    **scan,
                    columns=columns,
                )

    return scans
