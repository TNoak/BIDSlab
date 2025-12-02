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
from abidskit.common.specs_phenotype import MeasurementTool, PhenotypeColumn
from abidskit.common.specs_summary import Participant
from abidskit.settings import get_settings_values
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

COLUMNS_TO_REMOVE_FROM_TSV = {
    "columns",
    "name",
    "description",
    "term_url",
    "_participant",
}


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
        self.derivatives_path: pathlib.Path | None = None
        self.code_path: pathlib.Path | None = None
        self.stimuli_path: pathlib.Path | None = None
        self.phenotype_path: pathlib.Path | None = None

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

        override_validation = get_settings_values()["OVERRIDE_VALIDATION"]

        if self.name is None and not override_validation:
            raise FieldMissingError("Field `Name` is required in Dataset")
        if self.bids_version is None and not override_validation:
            raise FieldMissingError("Field `BIDSVersion` is required in Dataset")
        if self.readme_path is None and not override_validation:
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
        _ = dataset_description.pop("sourcedata_path", None)
        _ = dataset_description.pop("code_path", None)
        _ = dataset_description.pop("stimuli_path", None)
        _ = dataset_description.pop("phenotype_path", None)
        _ = dataset_description.pop("derivatives_path", None)
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

        self.write_phenotype(output_path=output_path, overwrite=overwrite)

        # write each participant data
        for participant in self.participants:
            path = pathlib.Path(output_path) / participant.participant_id
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            participant.write(path)

    def write_phenotype(  # noqa: C901
        self, output_path: os.PathLike | str, overwrite: bool = False
    ) -> None:
        output_path = pathlib.Path(output_path)

        if output_path.exists() and not overwrite:
            raise FileExistsError(
                f"The output path {output_path} already exists. "
                f"Set `overwrite=True` to overwrite existing files."
            )

        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)

        phenotypes = []
        measurement_tool_names = set()
        for participant in self.participants:
            if pht_list := participant.phenotype:
                phenotypes.append(pht_list)
                for pht in pht_list:
                    measurement_tool_names.add(pht.name)

        for toolname in measurement_tool_names:
            pht_tsv_path = output_path / "phenotype" / f"{toolname}.tsv"
            pht_json_path = output_path / "phenotype" / f"{toolname}.json"

            measurement_columns: Sequence[PhenotypeColumn] = []
            for phenotype_list in phenotypes:
                for phenotype in phenotype_list:
                    if phenotype.name == toolname and phenotype.columns:
                        measurement_columns = phenotype.columns
                        break

            # write phenotype json sidecar
            phenotype_description = {}
            for column in measurement_columns:
                column_dict = column.__dict__.copy()
                column_name = column_dict.pop("column_name")
                levels = column_dict.pop("_levels", None)

                phenotype_description[column_name] = column_dict

                if levels is not None:
                    phenotype_description = add_levels_to_dict(
                        levels, column_name, phenotype_description
                    )

            phenotype_description = clean_dict(phenotype_description)
            if not pht_json_path.parent.exists():
                pht_json_path.parent.mkdir(parents=True, exist_ok=True)
            json.dump(
                phenotype_description,
                pht_json_path.open("w", encoding="utf-8"),
                indent=4,
            )

            # write phenotype tsv
            rows = []
            for phenotype_list in phenotypes:
                for phenotype in phenotype_list:
                    if phenotype.name == toolname:
                        row = {}
                        if phenotype.participant:
                            row["participant_id"] = phenotype.participant.participant_id
                        for key, value in phenotype.__dict__.items():
                            if key not in COLUMNS_TO_REMOVE_FROM_TSV:
                                row[key] = value
                        rows.append(row)

            phenotype_df = pd.DataFrame(rows)
            phenotype_df.to_csv(pht_tsv_path, sep="\t", index=False)


def get_participants_from_files(
    dataset: Dataset,
    tsv_path: pathlib.Path | None,
    json_path: pathlib.Path | None,
) -> MutableSequence[Participant]:
    participants: MutableSequence[Participant] = []
    columns = []

    measurement_tools = get_phenotypes_from_files(dataset)

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
                phenotype=measurement_tools.get(participant_id, None),
                **participant,
            )
    else:
        dirs = dataset.root.iterdir()
        for directory in dirs:
            if directory.is_dir() and directory.name.startswith("sub-"):
                # TODO: Phenotype?
                add_object_to_sequence(
                    entity_list=participants,
                    entity_class=Participant,
                    base_path=dataset.root / directory.name,
                    participant_id=directory.name,
                    dataset=dataset,
                )

    return participants


def get_phenotypes_from_files(
    dataset: Dataset,
) -> Mapping[str, Sequence[MeasurementTool]]:
    measurement_tools: dict[str, MutableSequence] = {}

    if pht_path := dataset.phenotype_path:
        files = pht_path.iterdir()
        measurement_tool_names = set()
        for file in files:
            measurement_tool_names.add(file.stem)
        for toolname in measurement_tool_names:
            measurement_columns = []
            pht_tsv_path, pht_json_path = get_tsv_json_files(pht_path, toolname)

            if pht_json_path:
                column_data = parse_json_sidecar(pht_json_path)
                for column_name, column_values in column_data.items():
                    measurement_columns.append(
                        PhenotypeColumn(name=column_name, **column_values)
                    )

            if pht_tsv_path:
                data = parse_descriptive_tsv(pht_tsv_path)
                for pht_participant in data:
                    assert isinstance(pht_participant, dict)
                    participant_id = pht_participant.pop("participant_id", None)
                    if participant_id is None:
                        raise FieldMissingError(
                            f"Field `participant_id` is required as column in "
                            f"phenotype/{toolname}.tsv"
                        )
                    if not measurement_tools.get(participant_id, None):
                        measurement_tools[participant_id] = []
                    measurement_tools[participant_id].append(
                        MeasurementTool(
                            name=toolname,
                            columns=measurement_columns,
                            **pht_participant,
                        )
                    )

    return measurement_tools
