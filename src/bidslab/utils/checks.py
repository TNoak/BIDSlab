#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import pathlib
import re
from typing import TYPE_CHECKING, Any, Sequence
from warnings import warn

from uritools import isuri

from bidslab.settings import get_settings_value
from bidslab.utils.exceptions import (
    FieldMissingWarning,
    FieldPresentError,
    FieldPresentWarning,
    FileMissingError,
    InvalidURIError,
    MultipleFilesFoundError,
    VersionMismatchError,
    VersionMismatchWarning,
)
from bidslab.utils.string_manipulation import to_titlecase

if TYPE_CHECKING:
    from bidslab.common.specs_dataset import Dataset


def check_readme(dataset: "Dataset", files: Sequence[pathlib.Path]):
    readme_found = False

    for file in files:
        if re.match(r"^README(\.md|\.txt|\.rst)?$", file.name):
            if not readme_found:
                readme_found = True
            else:
                if not get_settings_value("OVERRIDE_VALIDATION"):
                    raise MultipleFilesFoundError(
                        "README[.md|.txt|.rst] file is already present."
                    )
                warn(
                    "Multiple README[.md|.txt|.rst] files found. Using the "
                    "first one found.",
                    FieldPresentWarning,
                )
                break
            dataset.readme_path = dataset.root / file

    if not readme_found and not get_settings_value("OVERRIDE_VALIDATION"):
        raise FileMissingError("README file is missing.")


def check_citation(dataset: "Dataset", files: Sequence[pathlib.Path]):
    for file in files:
        if re.match(r"^CITATION\.cff$", file.name):
            if dataset.authors is not None and not get_settings_value(
                "OVERRIDE_VALIDATION"
            ):
                raise FieldPresentError(
                    "Field `Authors` must be omitted in `dataset_description` when "
                    "`CITATION.cff` is present."
                )

            dataset.citation_path = dataset.root / file
            # TODO: Parse CITATION.cff
            # TODO: overwrite Name and DatasetDOI

            for attr in ["how_to_acknowledge", "license", "references_and_links"]:
                if getattr(dataset, attr, None) is not None:
                    warn(
                        f"Field `{to_titlecase(attr)}` should be omitted in "
                        f"`dataset_description` when `CITATION.cff` is present.",
                        FieldPresentWarning,
                    )


def check_license(dataset: "Dataset", files: Sequence[pathlib.Path]):
    for file in files:
        if re.match(r"^LICENSE(\.md|\.txt|\.rst)?$", file.name):
            dataset.license_path = dataset.root / file
            # TODO: Check if License in dataset_description matches LICENSE file content
            # TODO: Check if dataset.license is an abbreviation and warn if not
            if dataset.license is None and dataset.citation_path is None:
                warn(
                    "Field `License` is missing in `dataset_description` but LICENSE "
                    "file is present. Consider adding a short specification of the "
                    "license in `dataset_description`.",
                    FieldMissingWarning,
                )


def check_version(dataset: "Dataset", version: Any):
    if not isinstance(version, str):
        raise TypeError(
            "BIDS version must be a string."
        )  # for mypy, TODO: change to static type
    if not dataset.bids_version == version:
        if get_settings_value("IGNORE_VERSION"):
            warn(
                f"BIDS version mismatch! Expected: {dataset.bids_version}, "
                f"Found: {version}. Compatibility issues may arise.",
                VersionMismatchWarning,
            )
        elif not get_settings_value("OVERRIDE_VALIDATION"):
            raise VersionMismatchError(
                f"BIDS version mismatch! Expected: {dataset.bids_version}, "
                f"Found: {version}."
            )


def check_dataset_description_present(dataset: "Dataset"):
    if not (
        dataset.root / "dataset_description.json"
    ).exists() and not get_settings_value("OVERRIDE_VALIDATION"):
        raise FileMissingError("dataset_description.json file is missing.")


def check_if_valid_uri(uri: str):
    if not isuri(uri) and not get_settings_value("OVERRIDE_VALIDATION"):
        raise InvalidURIError(f"Value '{uri}' is not a valid URI.")


def check_files(dataset: "Dataset", files: Sequence[pathlib.Path]):
    check_readme(dataset, files)
    # TODO: Enable these checks later --> rewriting of tests required due to
    #  side effects
    # check_license(dataset, files)
    # check_citation(dataset, files)
    for file in files:
        # if re.match(r"README(\..*)?", file.name):
        #     if dataset.readme_path is None:
        #         dataset.readme_path = dataset.root / file
        #     elif not get_settings_values("OVERRIDE_VALIDATION"):
        #         raise MultipleFilesFoundError("Multiple README files found.")
        #     else:
        #         warn(
        #             "Multiple README files found. Using the first one found: "
        #             f"{dataset.readme_path.name}",
        #             MultipleFilesFoundWarning,
        #         )
        if re.match(r"CITATION\.cff", file.name):
            dataset.citation_path = dataset.root / file
        elif re.match(r"LICENSE(\..*)?", file.name):
            dataset.license_path = dataset.root / file
        # TODO: Check how to handle multiple license files
        if re.match(r"CHANGES(\..*)?", file.name):
            dataset.changes_path = dataset.root / file
        elif re.match(r"sourcedata", file.name):
            dataset.sourcedata_path = dataset.root / "sourcedata"
        elif re.match(r"code", file.name):
            dataset.code_path = dataset.root / "code"
        elif re.match(r"stimuli", file.name):
            dataset.stimuli_path = dataset.root / "stimuli"
        elif re.match(r"phenotype", file.name):
            dataset.phenotype_path = dataset.root / "phenotype"
        elif re.match(r"derivatives", file.name):
            dataset.derivatives_path = dataset.root / "derivatives"
