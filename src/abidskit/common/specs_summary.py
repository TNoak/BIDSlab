#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib
from typing import TYPE_CHECKING, Any, Mapping, MutableSequence, Sequence
from warnings import warn

import pandas as pd

from abidskit.common.base import Entity
from abidskit.common.specs_datatype import Datatype
from abidskit.common.specs_misc import Column
from abidskit.common.specs_phenotype import MeasurementTool
from abidskit.settings import get_settings_value
from abidskit.utils.dict_manipulation import ManipulateKeysOption, clean_dict
from abidskit.utils.exceptions import FieldMissingError, TopLevelEntityNotLinkedWarning
from abidskit.utils.helpers import (
    add_object_to_sequence,
    append_path,
    get_matching_subpaths,
    get_tsv_json_files,
    parse_descriptive_tsv,
    parse_json_sidecar,
    write_json,
)

if TYPE_CHECKING:
    from abidskit.common.specs_dataset import Dataset

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
    "emg",
}


class Scan:
    def __init__(
        self, base_path: os.PathLike | str, filename: os.PathLike | str, **kwargs: Any
    ) -> None:
        self.filename: pathlib.Path = pathlib.Path(filename)
        self.columns: Sequence[str] | None = None

        self.root: pathlib.Path = pathlib.Path(base_path)

        for key, value in kwargs.items():
            setattr(self, key, value)

        if not filename:
            raise FieldMissingError("Field `Filename` is required in Scan")

    def __repr__(self) -> str:
        return f"<Scan filename={self.filename}>"

    @property
    def filepath(self) -> pathlib.Path:
        return self.root / self.filename


class Session(Entity):
    def __init__(
        self,
        base_path: os.PathLike | str,
        session_id: str,
        virtual_entity: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            _entity_id=session_id, _entity_name="ses", _virtual_entity=virtual_entity
        )
        self.session_id: str = self._entity_id  # !: This is required
        self.acq_time: str | None = None
        self.pathology: str | int | None = None  # TODO: check if same as in samples
        self.hed: str | None = None

        # TODO: add columns

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._participant: Participant | None = None

        self._scans: Sequence[Scan] | None = None
        self._datatypes: dict[str, Datatype] | None = None

        for key, value in kwargs.items():
            setattr(self, key, value)

        if not session_id:
            raise FieldMissingError("Field `Session_id` is required in Session")

    def __repr__(self) -> str:
        return f"<Session id={self.session_id}>"

    @property
    def participant(self) -> "Participant | None":
        if self._participant:
            return self._participant

        warn(
            "Session is not linked to a Participant object.",
            TopLevelEntityNotLinkedWarning,
        )
        return self._participant

    @participant.setter
    def participant(self, value: "Participant") -> None:
        self._participant = value

    @property
    def scans(self) -> Sequence[Scan] | None:
        if not self._scans:
            dataset_root = self.root

            if participant := self.participant:
                if participant.dataset:
                    dataset_root = participant.dataset.root
                else:
                    warn(
                        "Top-level Participant object of this Session has no linked "
                        "top-level Dataset object. Therefore this Session's 'root' "
                        "attribute is used for Scan detection.",
                        TopLevelEntityNotLinkedWarning,
                    )
            else:
                warn(
                    "Session is not linked to a Participant object. Therefore "
                    "this session's 'root' attribute is used for scan detection.",
                    TopLevelEntityNotLinkedWarning,
                )

            self._scans = get_scans_from_files(self, dataset_root=dataset_root)
            if self._scans:
                return self._scans

            # TODO: implement automatic scan detection
            self._scans = []
            assert self.datatypes is not None
            for key in self.datatypes:
                match key:
                    case "motion":
                        # idk where to get acq_time from
                        files = list(self.datatypes[key].root.glob("*_motion.tsv"))
                        for file in files:
                            add_object_to_sequence(
                                entity_list=self._scans,
                                entity_class=Scan,
                                base_path=self.root,
                                filename="motion/" + file.name,
                            )
                    case "eeg":
                        files = list(self.datatypes[key].root.glob("*.vhdr"))
                        files.extend(list(self.datatypes[key].root.glob("*.set")))
                        for file in files:
                            add_object_to_sequence(
                                entity_list=self._scans,
                                entity_class=Scan,
                                base_path=self.root,
                                filename="eeg/" + file.name,
                            )
                    case _:
                        raise NotImplementedError
        return self._scans

    @scans.setter
    def scans(self, value: Sequence[Mapping] | Sequence[Scan]) -> None:
        # TODO: handle columns here
        if isinstance(value, Sequence):
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
    def datatypes(self) -> dict[str, Datatype]:
        if not self._datatypes:
            self._datatypes = {}
            for file in self.root.iterdir():
                if file.is_dir() and file.name in ALLOWED_DATATYPES:
                    self._datatypes.update(
                        {
                            file.name: Datatype(
                                base_path=file, datatype_name=file.name, session=self
                            )
                        }
                    )

        return self._datatypes

    @datatypes.setter
    def datatypes(
        self, value: Sequence[str] | Sequence[Datatype] | dict[str, Datatype]
    ) -> None:
        if isinstance(value, Sequence):
            if all(isinstance(entry, str) for entry in value):
                self._datatypes = {}
                for entry in value:
                    assert isinstance(entry, str)  # for mypy
                    if entry in ALLOWED_DATATYPES:
                        self._datatypes.update(
                            {
                                entry: Datatype(
                                    base_path=self.root / entry,
                                    datatype_name=entry,
                                    session=self,
                                )
                            }
                        )
            elif all(isinstance(entry, Datatype) for entry in value):
                self._datatypes = {}
                for entry in value:
                    assert isinstance(entry, Datatype)  # for mypy
                    self._datatypes.update({entry.datatype_name: entry})
        elif isinstance(value, dict):
            self._datatypes = value
        else:
            raise TypeError("Field `Datatypes` must be a list of Datatype objects")

    def get_top_level_entities(self) -> list[str | Any]:
        assert self.participant is not None
        entities = self.participant.get_top_level_entities()
        entities.append(self.session_id)
        return entities

    def write(self, output_path: os.PathLike | str) -> None:
        output_path = pathlib.Path(output_path)

        output_path_json = append_path(output_path, "_scans.json")
        output_path_tsv = append_path(output_path, "_scans.tsv")

        # write scans.tsv / scans.json file
        if self.scans:
            data_json = self.scans[0].columns
            data_tsv = pd.DataFrame(scan.__dict__ for scan in self.scans)
            data_tsv = data_tsv.drop(columns=["columns", "root"], errors="ignore")

            if isinstance(data_json, dict):
                write_json(content=data_json, output_path=output_path_json)
            data_tsv.to_csv(output_path_tsv, sep="\t", index=False, header=True)

        for datatype in self.datatypes.values():
            # Insert datatype level folder
            path = pathlib.Path(output_path.parent) / datatype.datatype_name
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            path /= output_path.name
            datatype.write(path)


class Participant(Entity):
    def __init__(
        self,
        base_path: os.PathLike | str,
        participant_id: str,
        virtual_entity: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            _entity_id=participant_id,
            _entity_name="sub",
            _virtual_entity=virtual_entity,
        )
        self.participant_id: str = participant_id  # !: This is required
        self.species: str | int | None = None
        if get_settings_value("SUPPORT_OLD_VERSIONS") and not self.species:
            self.species = "homo sapiens"
        self.age: int | None = None
        self.sex: str | None = None
        self.handedness: str | None = None
        self.strain: str | int | None = None
        self.strain_rrid: str | None = None
        self.hed: str | None = None

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._dataset: Dataset | None = None

        self.columns: Sequence[Column] | None = None
        self._phenotype: Sequence[MeasurementTool] | None = None

        self._sessions: dict[str, Session] | None = None

        for key, value in kwargs.items():
            setattr(self, key, value)

        if not participant_id:
            raise FieldMissingError("Field `Participant_id` is required in Participant")

    def __repr__(self) -> str:
        return f"<Participant id={self.participant_id}>"

    @property
    def dataset(self) -> "Dataset | None":
        if self._dataset:
            return self._dataset

        warn("Participant is not linked to a Dataset", TopLevelEntityNotLinkedWarning)
        return self._dataset

    @dataset.setter
    def dataset(self, value: "Dataset") -> None:
        self._dataset = value

    @property
    def phenotype(self) -> Sequence[MeasurementTool] | None:
        return self._phenotype

    @phenotype.setter
    def phenotype(
        self, value: Sequence[Mapping] | Sequence[MeasurementTool] | None
    ) -> None:
        if isinstance(value, Sequence):
            if all(isinstance(entry, Mapping) for entry in value):
                self._phenotype = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._phenotype.append(MeasurementTool(participant=self, **entry))
            elif all(isinstance(entry, MeasurementTool) for entry in value):
                for entry in value:
                    assert isinstance(entry, MeasurementTool)  # for mypy
                    entry.participant = self
                self._phenotype = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        elif not value:
            self._phenotype = None
        else:
            raise TypeError(
                "Field `Phenotype` must be a list of MeasurementTool objects or None"
            )

    @property
    def sessions(self) -> dict[str, Session]:
        if not self._sessions:
            tsv_path, _ = get_tsv_json_files(
                self.root, f"{self.participant_id}_sessions"
            )
            self._sessions = get_sessions_from_files(self, tsv_path=tsv_path)

            # If no sessions are found, create a default one
            if len(self._sessions) == 0:
                self._sessions.update(
                    {
                        "ses-00": Session(
                            base_path=self.root,
                            session_id="ses-00",
                            virtual_entity=True,
                            participant=self,
                        )
                    }
                )

        return self._sessions

    @sessions.setter
    def sessions(self, value: Sequence[Mapping] | Sequence[Session]) -> None:
        if isinstance(value, Sequence):
            if all(isinstance(entry, Mapping) for entry in value):
                self._sessions = {}
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._sessions.update(
                        {entry.session_id: Session(base_path=self.root, **entry)}  # type: ignore[attr-defined]
                    )
            elif all(isinstance(entry, Session) for entry in value):
                self._sessions = {}
                for entry in value:
                    assert isinstance(entry, Session)  # for mypy
                    self._sessions.update({entry.session_id: entry})
        else:
            raise TypeError("Field `Sessions` must be a list of Session objects")

    def list_sessions(self) -> pd.DataFrame:
        sessions_dataframe = pd.DataFrame()
        for session in self.sessions.values():
            session_dict = session.__dict__.copy()
            session_dict = clean_dict(
                session_dict,
                skip_keys_to_manipulate=ManipulateKeysOption.ALL_KEYS_MANIPULATE,
            )

            sessions_dataframe = pd.concat(
                [sessions_dataframe, pd.DataFrame([session_dict])],
                ignore_index=True,
            )
        sessions_dataframe.dropna(axis=1, how="all", inplace=True)
        return sessions_dataframe

    def get_top_level_entities(self) -> list[str | Any]:
        return [self.participant_id]

    def write(self, output_path: os.PathLike | str) -> None:
        output_path = pathlib.Path(output_path)

        # write sessions description to "sessions.tsv"
        if len(self.sessions) > 1:
            sessions_dataframe = self.list_sessions()
            sessions_dataframe.to_csv(
                output_path / f"{self.participant_id}_sessions.tsv",
                sep="\t",
                index=False,
            )

        # write each session data
        for session in self.sessions.values():
            if len(self.sessions) > 1:
                path = output_path / session.session_id
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
            else:
                path = output_path
            path /= self.participant_id
            path = (
                append_path(path, f"_{session.session_id}")
                if len(self.sessions) > 1
                else path
            )
            session.write(path)


def get_sessions_from_files(
    participant: Participant,
    tsv_path: pathlib.Path | None,
) -> dict[str, Session]:
    sessions: MutableSequence[Session] = []
    if tsv_path:
        data = parse_descriptive_tsv(tsv_path)
        for session in data:
            assert isinstance(session, dict)
            session_id = session.get("session_id")
            if session_id is None:
                raise FieldMissingError(
                    "Field `session_id` is required as column in sessions.tsv"
                )
            add_object_to_sequence(
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
                add_object_to_sequence(
                    entity_list=sessions,
                    entity_class=Session,
                    base_path=participant.root / directory.name,
                    session_id=directory.name,
                    participant=participant,
                )

    sessions_dict: dict[str, Session] = {
        session.session_id: session for session in sessions
    }
    return sessions_dict


def get_scans_from_files(
    session: Session,
    dataset_root: pathlib.Path,
) -> Sequence[Scan]:
    # For every level before sessions:
    # - scans.json can be in root, subject or session level
    # - scans.tsv can be in subject or session level and the one from the entity
    #   furthest down the hierarchy is used
    column_data = {}
    scans: Sequence[Scan] = []

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
                columns.append(Column(name=column_name, **column_values))

        if tsv_path and dir_level != dataset_root:
            scans = []
            data = parse_descriptive_tsv(tsv_path)
            for scan in data:
                add_object_to_sequence(
                    entity_list=scans,
                    entity_class=Scan,
                    base_path=session.root,
                    **scan,
                    columns=columns,
                )

    return scans
