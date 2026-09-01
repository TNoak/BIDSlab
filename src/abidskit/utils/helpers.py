#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import json
import os
import pathlib
import re
import shutil
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
    Iterator,
    MutableSequence,
    Sequence,
    TypeVar,
)
from warnings import catch_warnings, simplefilter, warn

import numpy as np
import pandas as pd

from abidskit._typing import MC, E, PEntity
from abidskit.settings import PackageFetching, PackageLoading, get_settings_value
from abidskit.utils.checks import (
    check_dataset_description_present,
    check_files,
)
from abidskit.utils.dict_manipulation import (
    ManipulateKeysOption,
    clean_dict,
)
from abidskit.utils.exceptions import (
    FieldNotValidError,
    FileTypeUnsupportedWarning,
    MultipleFilesFoundWarning,
    PathsSameWarning,
    TopLevelEntityNotLinkedWarning,
)
from abidskit.utils.string_manipulation import to_snakecase

if TYPE_CHECKING:
    from abidskit.common.base import Event
    from abidskit.common.specs_dataset import Dataset
    from abidskit.common.specs_summary import Scan

try:
    import datalad.api as dl
except ImportError:
    dl = None
    warn(
        "Datalad is not installed. Some functionalities may be limited.", ImportWarning
    )

T = TypeVar("T")

REQUIRED_ENTITIES_FOR_WRITING = {
    "tracksys",
    "task",
}


def set_attr_from_dict(obj: T, data: dict) -> None:
    data = clean_dict(
        data,
        skip_keys_to_manipulate=ManipulateKeysOption.ALL_KEYS_MANIPULATE,
        string_manipulation=to_snakecase,
        include_sequences=True,
    )
    for key, value in data.items():
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

    check_files(dataset, files)


def get_matching_subpaths(
    path: pathlib.Path, matches: Sequence[str], root: pathlib.Path
) -> list[pathlib.Path]:
    # Get matching subpaths in the root directory
    paths = list(path.relative_to(root).parents) + [path]
    matching_subpaths = [
        root / dir_level
        for dir_level in paths
        for match in matches
        if dir_level.match(match)
    ]
    return matching_subpaths[::-1]


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
            case ".tsv" | ".gz":
                if file.suffix == ".gz" and not file.stem.endswith(".tsv"):
                    warn(
                        f"File {file} has an unsupported extension. Only .tsv[.gz] and "
                        f".json are supported.",
                        FileTypeUnsupportedWarning,
                    )
                    continue
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


def add_object_to_sequence(
    entity_list: MutableSequence,
    entity_class: "type[E] | type[MC] | type[Scan] | type[Event]",
    **kwargs: Any,
) -> None:
    entity_instance = entity_class(**kwargs)
    entity_list.append(entity_instance)


def append_path(
    input_path: os.PathLike | str,
    appendix: str,
) -> pathlib.Path:
    path = pathlib.Path(input_path)
    return path.with_stem(path.stem + appendix)


def copy_file(
    source_path: os.PathLike | str,
    destination_path: os.PathLike | str,
) -> None:
    source_path = pathlib.Path(source_path)
    destination_path = pathlib.Path(destination_path)
    if source_path == destination_path:
        warn(
            "Source and destination paths are the same. Skipping copy.",
            PathsSameWarning,
        )
    elif source_path.exists():
        shutil.copy(source_path, destination_path)
    else:
        raise FileNotFoundError(f"Source file {source_path} does not exist.")


def write_entities(
    output_path: os.PathLike | str, entities: "Sequence[PEntity]" | Iterable[PEntity]
) -> None:
    if isinstance(entities, Iterable):
        entities = list(entities)
    output_path = pathlib.Path(output_path)
    for entity in entities:
        path = (
            append_path(output_path, f"_{entity._entity_id}")
            if len(entities) > 1 or entity._entity_name in REQUIRED_ENTITIES_FOR_WRITING
            else output_path
        )
        entity.write(path)


def write_json(content: dict[str, Any], output_path: os.PathLike | str) -> None:
    output_path = pathlib.Path(output_path)
    if content:
        json.dump(
            content,
            output_path.open("w", encoding="utf-8"),
            indent=4,
            ensure_ascii=False,
        )


def get_data() -> Any:
    def decorator(f):  # numpydoc ignore=GL08
        @wraps(f)
        def wrapper(*args, **kwargs):  # numpydoc ignore=GL08
            pkg_str = get_settings_value("DATASET_FETCHING_PACKAGE")
            if pkg_str in PackageFetching:
                pkg = eval(pkg_str)
            else:
                pkg = None
            path = kwargs.get("path")
            if not path.exists():
                if pkg:
                    if pkg.__name__ == "datalad.api":
                        pkg.get(path)
                    else:
                        raise ValueError(
                            f"Data retrieval for package {pkg.__name__} is not "
                            f"implemented."
                        )
                elif pkg is None:
                    raise ValueError(
                        f"Path '{path}' does not exist and no supported data fetching "
                        f"package is configured."
                    )
                else:
                    raise ValueError(
                        f"Package '{_pkg_str_to_pkg_name(pkg_str)}' is not available."
                    )
            return f(*args, **kwargs)

        return wrapper

    return decorator


@get_data()
def load_tsv_data(
    *, path: pathlib.Path, header: int | None = None
) -> pd.DataFrame | np.ndarray:
    """
    Load TSV data from a file using the specified data loading package.

    Parameters
    ----------
    path : pathlib.Path
        The path to the TSV file.
    header : int | None, optional
        The row number to use as the column names. Default is None.

    Returns
    -------
    pd.DataFrame | np.ndarray
        The loaded TSV data in a format depending on the data loading package.
    """
    data: pd.DataFrame | np.ndarray
    data_load_package = get_settings_value("DATA_LOADING_PACKAGE")
    if data_load_package == PackageLoading.PANDAS:
        if path.suffix == ".gz":
            data = pd.read_csv(path, sep="\t", header=header, compression="gzip")
        else:
            data = pd.read_csv(path, sep="\t", header=header)
    elif data_load_package == PackageLoading.NUMPY:
        data = np.loadtxt(path, delimiter="\t", skiprows=header or 0, encoding="utf-8")
    else:
        raise ValueError(
            f"Data loading for package {data_load_package} is not implemented."
        )
    return data


def _pkg_str_to_pkg_name(pkg_str: str) -> str:
    """
    Convert package string from settings to actual package name.

    Parameters
    ----------
    pkg_str : str
        The package string from settings.

    Returns
    -------
    str
        The actual package name.
    """
    match pkg_str:
        case "PackageFetching.DATALAD":
            return "datalad"
        case "PackageLoading.PANDAS":
            return "pandas"
        case "PackageLoading.NUMPY":
            return "numpy"
        case _:
            raise ValueError(f"Unknown package string: {pkg_str}")


def check_entity_mismatch(filename: str, entitylist: Sequence[str]) -> bool:
    # check if any entity in the string is also contained in the list
    # check if the string filename only contains entities in the list
    entities = filename.split("_")
    return set(entities).issubset(entitylist)
