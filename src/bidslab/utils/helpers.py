"""Helper functions for various tasks in the aBIDSkit package."""

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

import edf_reader
import numpy as np
import pandas as pd

from bidslab._typing import EC, EE, MC, E, PEntity
from bidslab.settings import PackageFetching, PackageLoading, get_settings_value
from bidslab.utils.checks import (
    check_dataset_description_present,
    check_files,
)
from bidslab.utils.dict_manipulation import (
    ManipulateKeysOption,
    clean_dict,
)
from bidslab.utils.exceptions import (
    FieldNotValidError,
    FileTypeUnsupportedWarning,
    MultipleFilesFoundWarning,
    PathsSameWarning,
    TopLevelEntityNotLinkedWarning,
)
from bidslab.utils.string_manipulation import to_snakecase

if TYPE_CHECKING:
    from bidslab.common.specs_dataset import Dataset
    from bidslab.common.specs_misc import Event
    from bidslab.common.specs_summary import Scan

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
    """
    Set attributes of an object from a dictionary.

    Parameters
    ----------
    obj : T
        The object whose attributes are to be set.
    data : dict
        A dictionary containing the attributes and their values to set.

    Raises
    ------
    FieldNotValidError
        If a key in the dictionary does not correspond to a valid attribute of the
        object.
    """
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
    """
    Parse a JSON sidecar file and return its contents as a dictionary.

    Parameters
    ----------
    sidecar_path : pathlib.Path
        The path to the JSON sidecar file.

    Returns
    -------
    dict
        The contents of the JSON sidecar file as a dictionary.

    Notes
    -----
    This function assumes that the JSON file is encoded in UTF-8 and wraps the
    ``json.load`` function for convenience.
    """
    with sidecar_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_descriptive_tsv(tsv_path: pathlib.Path) -> Iterator[dict]:
    """
    Parse a descriptive TSV file and yield each entry as a dictionary.

    Parameters
    ----------
    tsv_path : pathlib.Path
        The path to the TSV file.

    Yields
    ------
    dict
        Each entry in the TSV file as a dictionary, with keys corresponding to the
        column headers.
    """
    with tsv_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
        headers = lines[0].strip().split("\t")
        for line in lines[1:]:
            entries = line.strip().split("\t")
            entry_dict = dict(zip(headers, entries, strict=False))
            yield entry_dict


def get_root_files(dataset: "Dataset") -> None:
    """
    Get all files in the root directory of the dataset and apply basic checks.

    Parameters
    ----------
    dataset : Dataset
        The dataset object.

    Warnings
    --------
    This function changes the state of the dataset object.

    See Also
    --------
    check_dataset_description_present : Check for the presence of the dataset
        description file.
    check_files : Apply basic checks to the files in the root directory.
    """
    files = list(dataset.root.iterdir())
    check_dataset_description_present(dataset)

    check_files(dataset, files)


def get_matching_subpaths(
    path: pathlib.Path, matches: Sequence[str], root: pathlib.Path
) -> list[pathlib.Path]:
    """
    Get all subpaths of a given path that match specified patterns.

    Parameters
    ----------
    path : pathlib.Path
        The path to analyze.
    matches : Sequence[str]
        A sequence of glob patterns to match against the subpaths.
    root : pathlib.Path
        The root directory to which the subpaths are relative.

    Returns
    -------
    list[pathlib.Path]
        A list of subpaths that match the specified patterns.

    Notes
    -----
    The function generates all parent directories of the given path relative to
    the root directory including `path` itself and checks each against the provided
    glob-style patterns.
    """
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
    """
    Extract entity values from a file name based on the specified entity name.

    Parameters
    ----------
    path : pathlib.Path
        The path of the file from which to extract the entity.
    entity_name : str
        The name of the entity to extract.

    Returns
    -------
    dict[str, str]
        A dictionary containing the extracted entity and its value.
    """
    entities = {}
    entity_name = entity_name.replace(" ", "")
    pattern = re.compile(rf"(?P<entity>({entity_name}))-(?P<value>[a-zA-Z0-9]+)")

    for match in pattern.finditer(path.stem):
        entities[match.group("entity")] = match.group("value")

    return entities


def get_entity_with_ending_from_file(
    path: pathlib.Path,
    entity_name: str,
    file_ending: str,
) -> dict[str, str]:
    """
    Extract entity values from a file name based on the specified entity name.

    Parameters
    ----------
    path : pathlib.Path
        The path of the file from which to extract the entity.
    entity_name : str
        The name of the entity to extract.
    file_ending : str
        The ending the files need to have to be valid candidates.

    Returns
    -------
    dict[str, str]
        A dictionary containing the extracted entity and its value.
    """
    entities = {}
    entity_name = entity_name.replace(" ", "")
    pattern = re.compile(
        rf"(?P<entity>({entity_name}))-(?P<value>[a-zA-Z0-9]+)*{file_ending}"
    )

    for match in pattern.finditer(path.stem):
        entities[match.group("entity")] = match.group("value")

    return entities


def get_tsv_json_files(
    path: pathlib.Path, file_name: str
) -> tuple[pathlib.Path | None, pathlib.Path | None]:
    """
    Get TSV and JSON files matching the specified file name in the given path.

    Parameters
    ----------
    path : pathlib.Path
        The directory path to search for files.
    file_name : str
        The base name of the files to search for (without extension).

    Returns
    -------
    tuple[pathlib.Path | None, pathlib.Path | None]
        A tuple containing the paths to the found TSV and JSON files. If a file
        type is not found, its corresponding value in the tuple will be None. The first
        element is the TSV file path, the second element is the JSON file path.
    """
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


def get_edf_json_files(
    path: pathlib.Path, file_name: str
) -> tuple[pathlib.Path | None, pathlib.Path | None]:
    """
    Get EDF and JSON files matching the specified file name in the given path.

    Parameters
    ----------
    path : pathlib.Path
        The directory path to search for files.
    file_name : str
        The base name of the files to search for (without extension).

    Returns
    -------
    tuple[pathlib.Path | None, pathlib.Path | None]
        A tuple containing the paths to the found EDF and JSON files. If a file
        type is not found, its corresponding value in the tuple will be None. The first
        element is the EDF file path, the second element is the JSON file path.
    """
    files = path.glob(f"{file_name}.*")
    edf_path = None
    json_path = None
    for file in files:
        match file.suffix:
            case ".edf" | ".bdf":
                if not edf_path:
                    edf_path = file
                else:
                    warn(
                        f"Multiple EDF or BDF files found for {file_name}. "
                        f"Using the first one found: {edf_path.name}",
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
                    f"File {file} has an unsupported extension. Only .edf, "
                    f".bdf and .json are supported.",
                    FileTypeUnsupportedWarning,
                )
    return edf_path, json_path


def add_object_to_sequence(
    entity_list: MutableSequence,
    entity_class: "type[E] | type[EC] | type[EE] | type[MC] | type[Scan] | type[Event]",
    **kwargs: Any,
) -> None:
    """
    Create an instance of an entity and add it to a sequence.

    Parameters
    ----------
    entity_list : MutableSequence
        The sequence to which the instance will be added.
    entity_class : type[E] | type[EC] | type[EE] | type[MC] | type[Scan]
        The class of the instance to be created and added to the list.
    **kwargs : Any
        The keyword arguments to be passed to the constructor of the class.
    """
    entity_instance = entity_class(**kwargs)
    entity_list.append(entity_instance)


def append_path(
    input_path: os.PathLike | str,
    appendix: str,
) -> pathlib.Path:
    """
    Append a string to the stem (without file extension) of a given file path.

    Parameters
    ----------
    input_path : os.PathLike | str
        The original file path.
    appendix : str
        The string to append to the stem of the file path.

    Returns
    -------
    pathlib.Path
        The modified file path with the appended string in the stem.
    """
    path = pathlib.Path(input_path)
    return path.with_stem(path.stem + appendix)


def copy_file(
    source_path: os.PathLike | str,
    destination_path: os.PathLike | str,
) -> None:
    """
    Copy a file from source to destination.

    Parameters
    ----------
    source_path : os.PathLike | str
        The path to the source file.
    destination_path : os.PathLike | str
        The path to the destination file.
    """
    source_path = pathlib.Path(source_path)
    destination_path = pathlib.Path(destination_path)
    # TODO: add overwrite functionality / checks
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
    """
    Write multiple entities to disk.

    Parameters
    ----------
    output_path : os.PathLike | str
        The base output path where entities should be written.
    entities : Sequence[PEntity]
        A sequence of entities to write.

    Notes
    -----
    A new subdirectory is created for each entity if there are multiple entities
    or if the entity is mandatory for writing.
    """
    output_path = pathlib.Path(output_path)
    for entity in entities:
        path = (
            append_path(output_path, f"_{entity._entity_id}")
            if not entity._virtual_entity
            or entity._entity_name in REQUIRED_ENTITIES_FOR_WRITING
            else output_path
        )
        entity.write(path)


def write_json(content: dict[str, Any], output_path: os.PathLike | str) -> None:
    """
    Write a dictionary as a JSON file to the specified output path.

    Parameters
    ----------
    content : dict[str, Any]
        The dictionary content to write to the JSON file.
    output_path : os.PathLike | str
        The path where the JSON file should be written.
    """
    output_path = pathlib.Path(output_path)
    if content:
        json.dump(
            content,
            output_path.open("w", encoding="utf-8"),
            indent=4,
            ensure_ascii=False,
        )


def get_data() -> Any:
    """
    Decorator to fetch data using the configured data fetching package.

    Returns
    -------
    Any
        The decorated function with data fetching capability.
    """

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
            try:
                data = pd.read_csv(path, sep="\t", header=header, compression="gzip")
            except pd.errors.EmptyDataError:
                data = pd.DataFrame()
        else:
            try:
                data = pd.read_csv(path, sep="\t", header=header)
            except pd.errors.EmptyDataError:
                data = pd.DataFrame()
    elif data_load_package == PackageLoading.NUMPY:
        data = np.loadtxt(path, delimiter="\t", skiprows=header or 0, encoding="utf-8")
    else:
        raise ValueError(
            f"Data loading for package {data_load_package} is not implemented."
        )
    return data


# TODO: write tests, especially with multi-channel data
@get_data()
def load_edf_data(*, path: pathlib.Path) -> pd.DataFrame | np.ndarray:
    data: pd.DataFrame | np.ndarray

    reader = edf_reader.EdfWrapper(str(path))
    data = reader.read_ts_channels_uutc(
        [channel["name"] for channel in reader.read_ts_channel_basic_info()],
        [None, None],
    )

    data_load_package = get_settings_value("DATA_LOADING_PACKAGE")
    if data_load_package == PackageLoading.PANDAS:
        data = pd.DataFrame(data.T)

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
