#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause
#
#  SPDX-License-Identifier: BSD-3-Clause

import re
from warnings import warn

from uritools import isuri

from abidskit.utils.exceptions import (
    FieldMissingWarning,
    FieldPresentError,
    FieldPresentWarning,
    FileMissingError,
    InvalidURIError,
    MultipleFilesFoundError,
    VersionMismatchWarning,
)
from abidskit.utils.string_manipulation import to_titlecase


def check_readme(dataset, files):
    readme_found = False

    for file in files:
        if re.match(r"^README(\.md|\.txt|\.rst)?$", file.name):
            if not readme_found:
                readme_found = True
            else:
                raise MultipleFilesFoundError(
                    "README[.md|.txt|.rst] file is already present."
                )
            dataset.readme_path = dataset.root / file

    if not readme_found:
        raise FileMissingError("README file is missing.")


def check_citation(dataset, files):
    for file in files:
        if re.match(r"^CITATION\.cff$", file.name):
            if dataset.authors is not None:
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


def check_license(dataset, files):
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


def check_version(cls, version):
    if not cls.bids_version == version:
        warn(
            f"BIDS version mismatch! Expected: {cls.bids_version}, Found: {version}. "
            f"Compatibility issues may arise.",
            VersionMismatchWarning,
        )


def check_dataset_description_present(dataset):
    if not (dataset.root / "dataset_description.json").exists():
        raise FileMissingError("dataset_description.json file is missing.")


def check_if_valid_uri(uri: str):
    if not isuri(uri):
        raise InvalidURIError(f"Value '{uri}' is not a valid URI.")
