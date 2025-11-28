#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import json
import os
import pathlib
from dataclasses import dataclass
from typing import Mapping, MutableSequence, Sequence

import pandas as pd

from abidskit.common.specs_misc import Column
from abidskit.common.specs_summary import Participant
from abidskit.utils.checks import check_if_valid_uri, check_version
from abidskit.utils.dict_manipulation import add_levels_to_dict, clean_dict
from abidskit.utils.exceptions import (
    FieldMissingError,
    VersionMismatchError,
)
from abidskit.utils.helpers import (
    add_object_to_sequence,
    copy_file,
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
        self, root: os.PathLike, bids_version: str, **kwargs: str | Mapping | Sequence
    ) -> None:
        self.name: str | None = None  # !: This is required
        self.bids_version: str = bids_version  # !: This is required
        self.hed_version: str | Sequence[str] | None = None
        self.dataset_links: Mapping[str, str] | None = None
        self.dataset_type: str | None = None
        self.license: str | None = None
        self.authors: Sequence[str] | None = None
        self.keywords: Sequence[str] | None = None
        self.acknowledgements: str | None = None
        self.how_to_acknowledge: str | None = None
        self.funding: Sequence[str] | None = None
        self.ethics_approvals: Sequence[str] | None = None
        self.references_and_links: Sequence[str] | None = None
        self.dataset_doi: str | None = None
        self._generated_by: Sequence[GeneratedBy] | None = None
        self._source_datasets: Sequence[SourceDataset] | None = None

        self.root: pathlib.Path = pathlib.Path(root)

        self.readme_path: pathlib.Path | None = None  # !: This is required
        self.citation_path: pathlib.Path | None = None
        self.changes_path: pathlib.Path | None = None
        self.license_path: pathlib.Path | None = None

        self.sourcedata_path: pathlib.Path | None = None
        self.code_path: pathlib.Path | None = None
        self.stimuli_path: pathlib.Path | None = None

        self._participants: Sequence[Participant] | None = None

        if kwargs:
            set_attr_from_dict(self, kwargs)

        if self.dataset_doi:
            check_if_valid_uri(self.dataset_doi)

    def __repr__(self) -> str:
        return (
            f"<BIDSDataset name={self.name} path={self.root} "
            f"bids_version={self.bids_version}>"
        )

    @property
    def generated_by(self) -> Sequence[GeneratedBy] | None:
        return self._generated_by

    @generated_by.setter
    def generated_by(self, value: Sequence[Mapping] | Sequence[GeneratedBy]) -> None:
        if isinstance(value, Sequence):
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
    def source_datasets(self) -> Sequence[SourceDataset] | None:
        return self._source_datasets

    @source_datasets.setter
    def source_datasets(
        self, value: Sequence[Mapping] | Sequence[SourceDataset]
    ) -> None:
        if isinstance(value, Sequence):
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
    def participants(self) -> Sequence[Participant]:
        if not self._participants:
            tsv_path, json_path = get_tsv_json_files(self.root, "participants")
            self._participants = get_participants_from_files(
                self, tsv_path=tsv_path, json_path=json_path
            )

            # If no participants are found, create a default one
            if len(self._participants) == 0:
                self._participants.append(
                    Participant(
                        base_path=self.root, participant_id="sub-00", dataset=self
                    )
                )

        return self._participants

    @participants.setter
    def participants(self, value: Sequence[Mapping] | Sequence[Participant]) -> None:
        if isinstance(value, Sequence):
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

    def list_participants(self) -> pd.DataFrame:
        participants_dataframe = pd.DataFrame()
        for participant in self.participants:
            participant_dict = participant.__dict__.copy()
            participant_dict = clean_dict(participant_dict, keys_to_titlecase=False)

            participant_dict.pop("columns")
            participants_dataframe = pd.concat(
                [participants_dataframe, pd.DataFrame([participant_dict])],
                ignore_index=True,
            )
        participants_dataframe.dropna(axis=1, how="all", inplace=True)
        return participants_dataframe

    def _columns(self) -> set[Column]:
        columns_set = set()
        for participant in self.participants:
            for column in participant.columns if participant.columns else []:
                columns_set.add(column)
        return columns_set

    def write(self, output_path: os.PathLike | str, overwrite: bool = False) -> None:
        output_path = self.root if not output_path else output_path
        output_path = pathlib.Path(output_path)

        if output_path.exists() and not overwrite:
            raise FileExistsError(
                f"The output path {output_path} already exists. "
                f"Set `overwrite=True` to overwrite existing files."
            )

        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)

        # write dataset description to "dataset_description.json"
        output_path_dataset_description = output_path / "dataset_description.json"
        dataset_description = self.__dict__.copy()
        files_to_copy = [
            dataset_description.pop("readme_path", None),
            dataset_description.pop("changes_path", None),
            dataset_description.pop("license_path", None),
            dataset_description.pop("citation_path", None),
        ]
        # sourcedata = dataset_description.pop("sourcedata_path", None)
        # code = dataset_description.pop("code_path", None)
        # stimuli = dataset_description.pop("stimuli_path", None)
        dataset_description = clean_dict(dataset_description)
        json.dump(
            dataset_description,
            output_path_dataset_description.open("w", encoding="utf-8"),
            indent=4,
        )

        for file in files_to_copy:
            if file is not None:
                copy_file(file, output_path / file.name)

        # write participants description to "participants.tsv"
        participants_dataframe = self.list_participants()
        participants_dataframe.to_csv(
            output_path / "participants.tsv", sep="\t", index=False
        )

        # write participants.json sidecar if columns are present
        output_path_participant_description = output_path / "participants.json"

        participant_description = {}
        columns = self._columns()
        for column in columns:
            column_dict = column.__dict__.copy()
            column_dict.pop("column_name")
            levels = column_dict.pop("_levels", None)

            participant_description[column.column_name] = column_dict

            if levels is not None:
                participant_description = add_levels_to_dict(
                    levels, column.column_name, participant_description
                )

        participant_description = clean_dict(participant_description)
        json.dump(
            participant_description,
            output_path_participant_description.open("w", encoding="utf-8"),
            indent=4,
        )

        # write each participant data
        for participant in self.participants:
            path = pathlib.Path(output_path) / participant.participant_id
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            participant.write(path)


def get_participants_from_files(
    dataset: Dataset,
    tsv_path: pathlib.Path | None,
    json_path: pathlib.Path | None,
) -> MutableSequence[Participant]:
    participants: MutableSequence[Participant] = []
    columns = []

    if json_path:
        column_data = parse_json_sidecar(json_path)
        for column_name, column_values in column_data.items():
            columns.append(Column(name=column_name, **column_values))

    if tsv_path:
        data = parse_descriptive_tsv(tsv_path)
        for participant in data:
            assert isinstance(participant, dict)
            participant_id = participant.get("participant_id")
            if participant_id is None:
                raise FieldMissingError(
                    "Field `participant_id` is required as column in participants.tsv"
                )
            add_object_to_sequence(
                entity_list=participants,
                entity_class=Participant,
                base_path=dataset.root / participant_id,
                columns=columns,
                dataset=dataset,
                **participant,
            )
    else:
        dirs = dataset.root.iterdir()
        for directory in dirs:
            if directory.is_dir() and directory.name.startswith("sub-"):
                add_object_to_sequence(
                    entity_list=participants,
                    entity_class=Participant,
                    base_path=dataset.root / directory.name,
                    participant_id=directory.name,
                    dataset=dataset,
                )

    return participants
