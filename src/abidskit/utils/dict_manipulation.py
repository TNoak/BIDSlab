#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import pathlib
from dataclasses import asdict
from enum import IntEnum
from typing import TYPE_CHECKING, Callable, MutableMapping, Sequence

from abidskit.utils.string_manipulation import to_titlecase

if TYPE_CHECKING:
    from abidskit.common.specs_misc import Level


class ManipulateKeysOption(IntEnum):
    """Enumeration for options in dictionary key manipulation."""

    NO_MANIPULATION = -1
    ALL_KEYS_MANIPULATE = 0
    SKIP_TOP_LEVEL_MANIPULATE = 1


def manipulate_dictkeys(
    dict_input: dict,
    string_manipulation: Callable[[str], str] = to_titlecase,
) -> dict:
    """
    Convert all keys in the dictionary with the manipulation function recursively.


def dict_keys_to_titlecase(dict_input: dict) -> dict:
    dict_output = {}
    for key, value in list(dict_input.items()):
        if key == "Levels":
            if all(isinstance(v, dict) for v in value.values()):
                for v_key, v_value in value.items():
                    value[v_key] = manipulate_dictkeys(
                        v_value, string_manipulation=string_manipulation
                    )
            dict_output[string_manipulation(key)] = value
            continue
        if isinstance(value, dict):
            dict_output[string_manipulation(key)] = manipulate_dictkeys(
                value, string_manipulation=string_manipulation
            )
        else:
            dict_output[string_manipulation(key)] = value

    return dict_output


def clean_dict(
    dict_input: dict,
    skip_keys_to_manipulate: ManipulateKeysOption = (
        ManipulateKeysOption.ALL_KEYS_MANIPULATE
    ),
    include_sequences: bool = False,
    string_manipulation: Callable[[str], str] = to_titlecase,
) -> dict:
    """
    Clean the input dictionary.

    Remove None values, private fields, convert paths to strings,
    and optionally convert keys via the manipulation function in `kwargs`.

    Parameters
    ----------
    dict_input : dict
        The input dictionary.
    skip_keys_to_manipulate : {0, -1, 1}
        Option to control title casing of keys. Must be one of:

        - -1: Do not convert any keys.

        - 0: Convert all keys.

        - 1: Convert all keys except top-level keys.
    include_sequences : bool, optional
        Whether to include sequence values in the cleaning process. Default is False.
    string_manipulation : Callable[[str], str], optional
        A function to manipulate the keys of the dictionary. Default is `to_titlecase`.

    Returns
    -------
    dict
        The cleaned dictionary.

    See Also
    --------
    abidskit.utils.dict_manipulation.delete_none_from_dict
        Function to delete None values from a dictionary.
    abidskit.utils.dict_manipulation.delete_private_fields_from_dict
        Function to delete private fields from a dictionary.
    abidskit.utils.dict_manipulation.manipulate_dictkeys
        Function to convert dictionary keys using a manipulation function.
    abidskit.utils.dict_manipulation.dict_paths_to_strings
        Function to convert pathlib.Path values to strings in a dictionary.
    """
    dict_output = delete_none_from_dict(dict_input)
    dict_output = delete_private_fields_from_dict(dict_output)
    dict_output = dict_paths_to_strings(dict_output)
    _ = dict_output.pop("root", None)
    # Will raise DeprecationWarning due to __contains__ raising TypeError in Python
    # versions < 3.12
    if skip_keys_to_manipulate not in ManipulateKeysOption:
        raise ValueError(
            f"keys_to_titlecase must be -1, 0, or 1, got {skip_keys_to_manipulate}"
        )
    if skip_keys_to_manipulate == ManipulateKeysOption.ALL_KEYS_MANIPULATE:
        dict_output = manipulate_dictkeys(
            dict_output, string_manipulation=string_manipulation
        )
    if skip_keys_to_manipulate == ManipulateKeysOption.SKIP_TOP_LEVEL_MANIPULATE:
        for key, value in list(dict_output.items()):
            dict_output[key] = manipulate_dictkeys(
                value, string_manipulation=string_manipulation
            )
    if include_sequences:
        for key, value in dict_output.items():
            match value:
                case list() if any(isinstance(item, dict) for item in value):
                    dict_output[key] = [
                        clean_dict(
                            item,
                            skip_keys_to_manipulate,
                            include_sequences,
                            string_manipulation,
                        )
                        if isinstance(item, dict)
                        else item
                        for item in value
                    ]
    return dict_output


def dict_paths_to_strings(dict_input: dict) -> dict:
    dict_output: dict[str, dict | str] = {}
    for key, value in list(dict_input.items()):
        if isinstance(value, dict):
            dict_output[key] = dict_paths_to_strings(value)
        else:
            if isinstance(value, pathlib.Path):
                dict_output[key] = str(value)
            else:
                dict_output[key] = value

    return dict_output


def delete_private_fields_from_dict(dict_input: MutableMapping) -> dict:
    dict_output = {}
    for key, value in list(dict_input.items()):
        if isinstance(value, dict):
            dict_output[key] = delete_private_fields_from_dict(value)
        else:
            if not key.startswith("_"):
                dict_output[key] = value

    return dict_output


def delete_none_from_dict(dict_input: dict) -> dict:
    """Delete None values recursively from all of the dictionaries.

    From: https://stackoverflow.com/questions/33797126/proper-way-to-remove-keys-in-dictionary-with-none-values-in-python
    """
    for key, value in list(dict_input.items()):
        if isinstance(value, dict):
            delete_none_from_dict(value)
        elif value is None:
            del dict_input[key]
        elif isinstance(value, list):
            for v_i in value:
                if isinstance(v_i, dict):
                    delete_none_from_dict(v_i)

    return dict_input


def add_levels_to_dict(
    levels: "Sequence[Level]", column_name: str, output_dict: dict
) -> dict:
    levels_dict = {}
    for level in levels:
        level_value = asdict(level)
        level_name = level_value.pop("level_name")
        level_value = clean_dict(
            level_value,
            skip_keys_to_manipulate=ManipulateKeysOption.ALL_KEYS_MANIPULATE,
        )
        if list(level_value.keys()) == ["description"]:
            level_value = level_value["description"]
        levels_dict[level_name] = level_value

    output_dict[column_name]["Levels"] = levels_dict
    return output_dict
