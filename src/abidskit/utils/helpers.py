#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import json
import pathlib
import re
from typing import TYPE_CHECKING, Any, Iterable, Iterator, List, Mapping, TypeVar
from warnings import catch_warnings, simplefilter, warn

from abidskit.utils.checks import check_dataset_description_present
from abidskit.utils.exceptions import (
    FieldNotValidError,
    FileTypeUnsupportedWarning,
    MultipleFilesFoundError,
    MultipleFilesFoundWarning,
    TopLevelEntityNotLinkedWarning,
)
from abidskit.utils.string_manipulation import to_snakecase

if TYPE_CHECKING:
    from abidskit.common.specs_description import Dataset
    from abidskit.common.specs_summary import Participant, Scan, Session

T = TypeVar("T")


def set_attr_from_dict(obj: T, data: Mapping) -> None:
    for key, value in data.items():
        key = to_snakecase(key)
        with catch_warnings():
            simplefilter("ignore", category=TopLevelEntityNotLinkedWarning)
            if hasattr(obj, key):
                setattr(obj, key, value)
            else:
                raise FieldNotValidError(
                    f"Field {key} is not valid in {obj.__class__.__name__}"
                ) from None


def parse_json_sidecar(sidecar_path: pathlib.Path) -> dict:
    with sidecar_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_descriptive_tsv(tsv_path: pathlib.Path) -> Iterator[dict]:
    with tsv_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
        headers = lines[0].strip().split("\t")
        for line in lines[1:]:
            entries = line.strip().split("\t")
            entry_dict = dict(zip(headers, entries, strict=False))
            yield entry_dict


def get_root_files(dataset: "Dataset") -> None:
    files = list(dataset.root.iterdir())
    check_dataset_description_present(dataset)

    for file in files:
        if re.match(r"README(\..*)?", file.name):
            if dataset.readme_path is None:
                dataset.readme_path = dataset.root / file
            else:
                raise MultipleFilesFoundError("Multiple README files found.")
        elif re.match(r"CITATION\.cff", file.name):
            dataset.citation_path = dataset.root / file
        elif re.match(r"LICENSE(\..*)?", file.name):
            dataset.license_path = dataset.root / file
            # TODO: Check how to handle multiple license files
        elif re.match(r"CHANGES(\..*)?", file.name):
            dataset.changes_path = dataset.root / file
        elif re.match(r"sourcedata", file.name):
            dataset.sourcedata_path = dataset.root / "sourcedata"
        elif re.match(r"code", file.name):
            dataset.code_path = dataset.root / "code"
        elif re.match(r"stimuli", file.name):
            dataset.stimuli_path = dataset.root / "stimuli"


def get_matching_subpaths(
    path: pathlib.Path, matches: Iterable[str], root: pathlib.Path
) -> list[pathlib.Path]:
    # Get matching subpaths in the root directory
    paths = list(path.relative_to(root).parents) + [path]
    return [
        root / dir_level
        for dir_level in paths
        for match in matches
        if dir_level.match(match)
    ]


def get_entity_from_file(path: pathlib.Path, entity_name: str) -> dict[str, str]:
    entities = {}
    entity_name = entity_name.replace(" ", "")
    pattern = re.compile(rf"(?P<entity>({entity_name}))-(?P<value>[a-zA-Z0-9]+)")

    for match in pattern.finditer(path.stem):
        entities[match.group("entity")] = match.group("value")

    return entities


def get_tsv_json_files(
    path: pathlib.Path, file_name: str
) -> tuple[pathlib.Path | None, pathlib.Path | None]:
    files = path.glob(f"{file_name}.*")
    tsv_path = None
    json_path = None
    for file in files:
        match file.suffix:
            case ".tsv":
                if not tsv_path:
                    tsv_path = file
                else:
                    warn(
                        f"Multiple TSV files found for {file_name}. Using the first "
                        f"one found: {tsv_path.name}",
                        MultipleFilesFoundWarning,
                    )
                continue
            case ".json":
                if not json_path:
                    json_path = file
                else:
                    warn(
                        f"Multiple JSON files found for {file_name}. Using the first "
                        f"one found: {json_path.name}",
                        MultipleFilesFoundWarning,
                    )
                continue
            case _:
                warn(
                    f"File {file} has an unsupported extension. Only .tsv and .json "
                    f"are supported.",
                    FileTypeUnsupportedWarning,
                )
    return tsv_path, json_path


def add_entity_to_list(
    entity_list: List,
    entity_class: "type[Participant] | type[Session] | type[Scan]",
    **kwargs: Any,
) -> None:
    entity_instance = entity_class(**kwargs)
    entity_list.append(entity_instance)
