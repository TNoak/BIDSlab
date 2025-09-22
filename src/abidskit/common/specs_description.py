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
from dataclasses import dataclass
from typing import Iterable, Mapping

from abidskit.common.specs_misc import Column
from abidskit.common.specs_summary import Participant
from abidskit.utils.checks import check_if_valid_uri, check_version
from abidskit.utils.exceptions import (
    FieldMissingError,
    VersionMismatchError,
)
from abidskit.utils.helpers import (
    get_root_files,
    get_tsv_json_files,
    parse_descriptive_tsv,
    parse_json_sidecar,
    set_attr_from_dict,
)


@dataclass(slots=True)
class SourceDataset:
    url: str | None = None
    doi: str | None = None
    version: str | None = None

    def __post_init__(self) -> None:
        if self.url:
            check_if_valid_uri(self.url)
        if self.doi:
            check_if_valid_uri(self.doi)

    def __repr__(self) -> str:
        return f"<SourceDataset url={self.url} doi={self.doi} version={self.version}>"


@dataclass(slots=True)
class Container:
    type: str | None = None
    tag: str | None = None
    uri: str | None = None

    def __post_init__(self) -> None:
        if self.uri:
            check_if_valid_uri(self.uri)

    def __repr__(self) -> str:
        return f"<Container type={self.type} tag={self.tag} uri={self.uri}>"


class GeneratedBy:
    def __init__(self, **kwargs: str | Mapping | Container) -> None:
        self.name: str | None = None  # !: This is required
        self.version: str | None = None
        self.description: str | None = None
        self.code_url: str | None = None
        self._container: Container | None = None

        if kwargs:
            set_attr_from_dict(self, kwargs)

        if self.name is None:
            raise FieldMissingError("Field `Name` is required in GeneratedBy")

    def __post_init__(self) -> None:
        if self.code_url:
            check_if_valid_uri(self.code_url)

    def __repr__(self) -> str:
        return f"<GeneratedBy name={self.name} version={self.version}>"

    @property
    def container(self) -> Container | None:
        return self._container

    @container.setter
    def container(self, value: Mapping | Container) -> None:
        if isinstance(value, Mapping):
            self._container = Container(**value)
        elif isinstance(value, Container):
            self._container = value
        else:
            raise TypeError("Field `Container` must be a Container object")


class Dataset:
    def __init__(
        self, root: os.PathLike, bids_version: str, **kwargs: str | Mapping | Iterable
    ) -> None:
        self.name: str | None = None  # !: This is required
        self.bids_version: str = bids_version  # !: This is required
        self.hed_version: str | Iterable[str] | None = None
        self.dataset_links: Mapping[str, str] | None = None
        self.dataset_type: str | None = None
        self.license: str | None = None
        self.authors: Iterable[str] | None = None
        self.keywords: Iterable[str] | None = None
        self.acknowledgements: str | None = None
        self.how_to_acknowledge: str | None = None
        self.funding: Iterable[str] | None = None
        self.ethics_approvals: Iterable[str] | None = None
        self.references_and_links: Iterable[str] | None = None
        self.dataset_doi: str | None = None
        self._generated_by: Iterable[GeneratedBy] | None = None
        self._source_datasets: Iterable[SourceDataset] | None = None

        self.root: pathlib.Path = pathlib.Path(root)

        self.readme_path = None  # !: This is required
        self.citation_path = None
        self.changes_path = None
        self.license_path = None

        self.sourcedata_path = None
        self.code_path = None
        self.stimuli_path = None

        self._participants: Iterable[Participant] | None = None

        if kwargs:
            set_attr_from_dict(self, kwargs)

        if self.dataset_doi:
            check_if_valid_uri(self.dataset_doi)

    def __repr__(self) -> str:
        return (
            f"<Dataset name={self.name} path={self.root} "
            f"bids_version={self.bids_version}>"
        )

    @property
    def generated_by(self) -> Iterable[GeneratedBy] | None:
        return self._generated_by

    @generated_by.setter
    def generated_by(self, value: Iterable[Mapping] | Iterable[GeneratedBy]) -> None:
        if isinstance(value, Iterable):
            if all(isinstance(entry, Mapping) for entry in value):
                self._generated_by = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    gen_by = GeneratedBy(**entry)

                    self._generated_by.append(gen_by)
            elif all(isinstance(entry, GeneratedBy) for entry in value):
                self._generated_by = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `GeneratedBy` must be a list of GeneratedBy objects")

    @property
    def source_datasets(self) -> Iterable[SourceDataset] | None:
        return self._source_datasets

    @source_datasets.setter
    def source_datasets(
        self, value: Iterable[Mapping] | Iterable[SourceDataset]
    ) -> None:
        if isinstance(value, Iterable):
            if all(isinstance(entry, Mapping) for entry in value):
                self._source_datasets = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._source_datasets.append(SourceDataset(**entry))
            elif all(isinstance(entry, SourceDataset) for entry in value):
                self._source_datasets = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError(
                "Field `SourceDatasets` must be a list of SourceDataset objects"
            )

    @property
    def participants(self) -> Iterable[Participant]:
        if not self._participants:
            tsv_path, json_path = get_tsv_json_files(self.root, "participants")
            columns = []
            self._participants = []
            if json_path:
                column_data = parse_json_sidecar(json_path)
                for column_name, column_values in column_data.items():
                    columns.append(Column(column_name=column_name, **column_values))
            if tsv_path:
                data = parse_descriptive_tsv(tsv_path)
                for participant in data:
                    self._participants.append(
                        Participant(
                            base_path=self.root / participant.get("participant_id"),
                            columns=columns,
                            dataset=self,
                            **participant,
                        )
                    )
            else:
                dirs = self.root.iterdir()
                for directory in dirs:
                    if directory.is_dir() and directory.name.startswith("sub-"):
                        self._participants.append(
                            Participant(
                                base_path=self.root / directory.name,
                                participant_id=directory.name,
                                dataset=self,
                            )
                        )

            # If no participants are found, create a default one
            if not self._participants:
                self._participants.append(
                    Participant(
                        base_path=self.root, participant_id="sub-00", dataset=self
                    )
                )

        return self._participants

    @participants.setter
    def participants(self, value: Iterable[Mapping] | Iterable[Participant]) -> None:
        # TODO: handle columns here
        if isinstance(value, Iterable):
            if all(isinstance(entry, Mapping) for entry in value):
                self._participants = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._participants.append(
                        Participant(
                            base_path=self.root / entry.get("participant_id", "sub-01"),
                            dataset=self,
                            **entry,
                        )
                    )
            elif all(isinstance(entry, Participant) for entry in value):
                self._participants = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError(
                "Field `Participants` must be a list of Participant objects"
            )

    def load(self) -> None:
        get_root_files(self)

        data = parse_json_sidecar(self.root / "dataset_description.json")

        try:
            check_version(self, data.get("BIDSVersion", None))
        except VersionMismatchError:
            raise VersionMismatchError(
                f"The version of the dataset you tried to load "
                f"{data.get('BIDSVersion', None)} is not the same as the one you "
                f"specified {self.bids_version}."
            ) from None

        set_attr_from_dict(self, data)

        if self.name is None:
            raise FieldMissingError("Field `Name` is required in Dataset")
        if self.bids_version is None:
            raise FieldMissingError("Field `BIDSVersion` is required in Dataset")
        if self.readme_path is None:
            raise FieldMissingError("File `README` is required")
