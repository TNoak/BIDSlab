#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import pathlib
from dataclasses import asdict
from typing import Sequence

from abidskit.common.specs_misc import Level
from abidskit.utils.string_manipulation import to_titlecase


def dict_keys_to_titlecase(dict_input: dict) -> dict:
    dict_output = {}
    for key, value in list(dict_input.items()):
        if isinstance(value, dict):
            dict_output[to_titlecase(key)] = dict_keys_to_titlecase(value)
        else:
            dict_output[to_titlecase(key)] = value

    return dict_output


def clean_dict(dict_input: dict, keys_to_titlecase: bool = True) -> dict:
    dict_output = delete_none_from_dict(dict_input)
    dict_output = delete_private_fields_from_dict(dict_output)
    dict_output = dict_paths_to_strings(dict_output)
    _ = dict_output.pop("root", None)
    if keys_to_titlecase:
        dict_output = dict_keys_to_titlecase(dict_output)
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


def delete_private_fields_from_dict(dict_input: dict) -> dict:
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
        level_value = clean_dict(level_value, keys_to_titlecase=False)
        if list(level_value.keys()) == ["description"]:
            level_value = level_value["description"]
        levels_dict[level_name] = level_value

    output_dict[column_name]["Levels"] = levels_dict
    return output_dict
