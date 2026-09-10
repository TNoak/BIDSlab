"""Participant, session, and scan summary specification classes.

This module models hierarchical BIDS summary entities beneath a dataset:
participants, sessions, scans, and helper functions for discovering them from
standard TSV/JSON files and directory layouts.
"""

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
    """
    Represent one entry in a BIDS scans table.

    Parameters
    ----------
    base_path : os.PathLike or str
        Base directory used to resolve the recorded filename.
    filename : os.PathLike or str
        Relative path stored in ``*_scans.tsv``.
    **kwargs
        Additional scan metadata such as acquisition time and HED tags.

    Attributes
    ----------
    filename : pathlib.Path
        Relative scan filename.
    acq_time : str | None
        Acquisition timestamp from the scans table.
    hed : str | None
        Optional HED annotation string.
    columns : Sequence[str] | None
        Optional list of column names originating from the sidecar metadata.
    filepath : pathlib.Path
        Resolved path returned by :py:attr:`filepath`.

    Raises
    ------
    FieldMissingError
        If ``filename`` is empty.

    Notes
    -----
    BIDS permits ``*_scans.tsv`` files at subject and session levels to describe
    data files and acquisition times.

    See Also
    --------
    :py:class:`Session`
        Session entity that owns scan entries.
    """

    def __init__(
        self, base_path: os.PathLike | str, filename: os.PathLike | str, **kwargs: Any
    ) -> None:
        """
        Initialize a scan entry.

        Parameters
        ----------
        base_path : os.PathLike or str
            Base directory used to resolve ``filename``.
        filename : os.PathLike or str
            Relative path from the scans table.
        **kwargs
            Additional scan metadata.
        """
        self.filename: pathlib.Path = pathlib.Path(filename)
        self.acq_time: str | None = None
        self.hed: str | None = None
        self.columns: Sequence[str] | None = None

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._session: Session | None = None

        for key, value in kwargs.items():
            setattr(self, key, value)

        if not filename:
            raise FieldMissingError("Field `Filename` is required in Scan")

    def __repr__(self) -> str:
        """Return a string representation of the scan entry."""
        return f"<Scan filename={self.filename}>"

    @property
    def filepath(self) -> pathlib.Path:
        """
        Get the resolved filesystem path for the scan file.

        Returns
        -------
        pathlib.Path
            Path composed from :attr:`root` and :attr:`filename`.

        Notes
        -----
        Reading this property has no side effects.
        """
        return self.root / self.filename

    @property
    def session(self) -> "Session | None":
        """
        Get the session linked to this scan.

        Returns
        -------
        Session | None
            Linked session, or ``None`` when detached.
        """
        if self._session:
            return self._session

        warn("Scan is not linked to a Session object.", TopLevelEntityNotLinkedWarning)
        return self._session

    @session.setter
    def session(self, value: "Session") -> None:
        """
        Link the scan to a session.

        Parameters
        ----------
        value : Session
            Parent session object.
        """
        self._session = value


class Session(Entity):
    """
    Represent a BIDS session belonging to a participant.

    Parameters
    ----------
    base_path : os.PathLike or str
        Filesystem path to the session directory.
    session_id : str
        BIDS session identifier including the ``ses-`` prefix.
    **kwargs
        Additional session metadata and linked entities.

    Attributes
    ----------
    session_id : str
        Session identifier.
    acq_time : str | None
        Session-level acquisition time if provided.
    pathology : str | int | None
        Optional pathology label.
    hed : str | None
        Optional HED annotation.
    scans : Sequence[Scan] | None
        Scan entries loaded from BIDS scans tables.
    datatypes : Sequence[Datatype]
        Datatype directories available inside the session.

    Raises
    ------
    FieldMissingError
        If ``session_id`` is missing.

    See Also
    --------
    :py:class:`Participant`
        Parent participant entity.
    :py:func:`get_scans_from_files`
        Helper used to load scans metadata.
    """

    def __init__(
        self, base_path: os.PathLike | str, session_id: str, **kwargs: Any
    ) -> None:
        """
        Initialize a session entity.

        Parameters
        ----------
        base_path : os.PathLike or str
            Directory containing session data.
        session_id : str
            Session identifier with ``ses-`` prefix.
        **kwargs
            Additional metadata and linked entities.
        """
        super().__init__(_entity_id=session_id, _entity_name="ses")
        self.session_id: str = self._entity_id  # !: This is required
        self.acq_time: str | None = None
        self.pathology: str | int | None = None  # TODO: check if same as in samples
        self.hed: str | None = None

        # TODO: add columns

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._participant: Participant | None = None

        self._scans: Sequence[Scan] | None = None
        self._datatypes: Sequence[Datatype] | None = None

        for key, value in kwargs.items():
            setattr(self, key, value)

        if not session_id:
            raise FieldMissingError("Field `Session_id` is required in Session")

    def __repr__(self) -> str:
        """Return a string representation of the session."""
        return f"<Session id={self.session_id}>"

    @property
    def participant(self) -> "Participant | None":
        """
        Get the participant that owns this session.

        Returns
        -------
        Participant | None
            Linked participant, or ``None`` if not attached.
        """
        if self._participant:
            return self._participant

        warn(
            "Session is not linked to a Participant object.",
            TopLevelEntityNotLinkedWarning,
        )
        return self._participant

    @participant.setter
    def participant(self, value: "Participant") -> None:
        """
        Link this session to a participant.

        Parameters
        ----------
        value : Participant
            Parent participant object.
        """
        self._participant = value

    @property
    def scans(self) -> Sequence[Scan] | None:
        """
        Get scans metadata associated with the session.

        Returns
        -------
        Sequence[Scan] | None
            Loaded scan entries, or ``None`` when no scans are found.

        Notes
        -----
        Scan metadata is discovered lazily from the closest applicable
        ``*_scans.tsv`` and ``*_scans.json`` files in the BIDS hierarchy.
        """
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

        # TODO: implement automatic scan detection
        return self._scans

    @scans.setter
    def scans(self, value: Sequence[Mapping] | Sequence[Scan]) -> None:
        """
        Set scan entries for the session.

        Parameters
        ----------
        value : Sequence[Mapping] or Sequence[Scan]
            Scan definitions or existing :py:class:`Scan` objects.

        Raises
        ------
        TypeError
            If ``value`` is not a valid scan sequence.
        """
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
    def datatypes(self) -> Sequence[Datatype]:
        """
        Get datatype directories contained in the session.

        Returns
        -------
        Sequence[Datatype]
            Datatype entities for allowed BIDS modality folders.
        """
        if not self._datatypes:
            self._datatypes = []
            for file in self.root.iterdir():
                if file.is_dir() and file.name in ALLOWED_DATATYPES:
                    self._datatypes.append(
                        Datatype(base_path=file, datatype_name=file.name, session=self)
                    )

        return self._datatypes

    @datatypes.setter
    def datatypes(self, value: Sequence[str] | Sequence[Datatype]) -> None:
        """
        Set datatype entities for the session.

        Parameters
        ----------
        value : Sequence[str] or Sequence[Datatype]
            Datatype names or existing datatype objects.

        Raises
        ------
        TypeError
            If ``value`` is not a supported datatype sequence.
        """
        if isinstance(value, Sequence):
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

    def write(self, output_path: os.PathLike | str) -> None:
        """
        Write the session contents to disk.

        Parameters
        ----------
        output_path : os.PathLike or str
            Output path stem used for datatype serialization.

        Returns
        -------
        None
            Datatype folders are written as side effects.
        """
        output_path = pathlib.Path(output_path)
        for datatype in self.datatypes:
            # Insert datatype level folder
            path = pathlib.Path(output_path.parent) / datatype.datatype_name
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            path /= output_path.name
            datatype.write(path)


class Participant(Entity):
    """
    Represent a BIDS participant and its nested session data.

    Parameters
    ----------
    base_path : os.PathLike or str
        Path to the participant directory.
    participant_id : str
        BIDS participant identifier including the ``sub-`` prefix.
    **kwargs
        Participant metadata, linked dataset reference, phenotype entries, and
        nested session definitions.

    Attributes
    ----------
    participant_id : str
        Participant identifier.
    species : str | int | None
        Species information, defaulting to ``"homo sapiens"`` for old-version
        compatibility when enabled.
    age : int | None
        Participant age.
    sex : str | None
        Participant sex.
    handedness : str | None
        Handedness label.
    strain : str | int | None
        Optional strain information for non-human subjects.
    strain_rrid : str | None
        RRID for the strain.
    hed : str | None
        Optional HED annotation.
    phenotype : Sequence[MeasurementTool] | None
        Phenotype measurement rows linked to the participant.
    sessions : Sequence[Session]
        Session entities nested below the participant.

    Raises
    ------
    FieldMissingError
        If ``participant_id`` is missing.

    Notes
    -----
    Participant metadata corresponds to the BIDS ``participants.tsv`` and
    ``participants.json`` files.
    """

    def __init__(
        self,
        base_path: os.PathLike | str,
        participant_id: str,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a participant entity.

        Parameters
        ----------
        base_path : os.PathLike or str
            Directory containing participant data.
        participant_id : str
            Participant identifier with ``sub-`` prefix.
        **kwargs
            Additional participant metadata and linked entities.
        """
        super().__init__(_entity_id=participant_id, _entity_name="sub")
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

        self._sessions: Sequence[Session] | None = None

        for key, value in kwargs.items():
            setattr(self, key, value)

        if not participant_id:
            raise FieldMissingError("Field `Participant_id` is required in Participant")

    def __repr__(self) -> str:
        """Return a string representation of the participant."""
        return f"<Participant id={self.participant_id}>"

    @property
    def dataset(self) -> "Dataset | None":
        """
        Get the dataset linked to this participant.

        Returns
        -------
        Dataset | None
            Parent dataset, or ``None`` if not linked.
        """
        if self._dataset:
            return self._dataset

        warn("Participant is not linked to a Dataset", TopLevelEntityNotLinkedWarning)
        return self._dataset

    @dataset.setter
    def dataset(self, value: "Dataset") -> None:
        """
        Link the participant to a dataset.

        Parameters
        ----------
        value : Dataset
            Parent dataset object.
        """
        self._dataset = value

    @property
    def phenotype(self) -> Sequence[MeasurementTool] | None:
        """
        Get phenotype measurements linked to the participant.

        Returns
        -------
        Sequence[MeasurementTool] | None
            Participant phenotype rows, or ``None`` when unavailable.
        """
        return self._phenotype

    @phenotype.setter
    def phenotype(
        self, value: Sequence[Mapping] | Sequence[MeasurementTool] | None
    ) -> None:
        """
        Set phenotype measurements for the participant.

        Parameters
        ----------
        value : Sequence[Mapping] or Sequence[MeasurementTool] or None
            Phenotype rows as mappings, measurement objects, or ``None``.

        Raises
        ------
        TypeError
            If ``value`` is not one of the supported forms.
        """
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
    def sessions(self) -> Sequence[Session]:
        """
        Get sessions belonging to the participant.

        Returns
        -------
        Sequence[Session]
            Session objects loaded from ``*_sessions.tsv`` or discovered from the
            directory structure.

        Notes
        -----
        A default ``ses-00`` session is created when no explicit sessions are
        found.
        """
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
    def sessions(self, value: Sequence[Mapping] | Sequence[Session]) -> None:
        """
        Set the sessions associated with the participant.

        Parameters
        ----------
        value : Sequence[Mapping] or Sequence[Session]
            Session definitions or existing session objects.

        Raises
        ------
        TypeError
            If ``value`` is not a supported session sequence.
        """
        if isinstance(value, Sequence):
            if all(isinstance(entry, Mapping) for entry in value):
                self._sessions = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._sessions.append(Session(base_path=self.root, **entry))
            elif all(isinstance(entry, Session) for entry in value):
                self._sessions = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Sessions` must be a list of Session objects")

    def list_sessions(self) -> pd.DataFrame:
        """
        Build a tabular summary of participant sessions.

        Returns
        -------
        pd.DataFrame
            DataFrame ready for serialization to ``*_sessions.tsv``.
        """
        sessions_dataframe = pd.DataFrame()
        for session in self.sessions:
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

    def write(self, output_path: os.PathLike | str) -> None:
        """
        Write the session contents to disk.

        Parameters
        ----------
        output_path : os.PathLike or str
            Output path stem used for datatype serialization.

        Returns
        -------
        None
            Datatype folders are written as side effects.
        """
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
        for session in self.sessions:
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
) -> MutableSequence[Session]:
    """
    Build session objects for a participant.

    Parameters
    ----------
    participant : Participant
        Participant owning the sessions.
    tsv_path : pathlib.Path | None
        Optional path to the participant ``*_sessions.tsv`` file.

    Returns
    -------
    MutableSequence[Session]
        Constructed session objects.

    Raises
    ------
    FieldMissingError
        If a sessions TSV row omits ``session_id``.
    """
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

    return sessions


def get_scans_from_files(
    session: Session,
    dataset_root: pathlib.Path,
) -> Sequence[Scan]:
    """
    Load scan table entries for a session from the BIDS hierarchy.

    Parameters
    ----------
    session : Session
        Session for which scan metadata should be loaded.
    dataset_root : pathlib.Path
        Root of the containing dataset, used to resolve inheritance levels.

    Returns
    -------
    Sequence[Scan]
        Scan objects parsed from the nearest applicable scans tables.

    Notes
    -----
    The BIDS inheritance principle is approximated by walking matching subject
    and session subpaths and applying the furthest-down ``*_scans.tsv`` file.
    """
    # For every level before sessions:
    # - scans.json can be in root, subject or session level
    # - scans.tsv can be in subject or session level and the one from the entity
    #   furthest down the hierarchy is used
    # TODO: make sure that the order of dir_levels is correct, such that dataset_root
    #  is first and session last
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
                    session=session,
                    **scan,
                    columns=columns,
                )

    return scans
