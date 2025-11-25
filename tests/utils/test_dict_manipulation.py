#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import pathlib

import pytest

import abidskit as abk


@pytest.fixture
def cleaned_sample_dict():
    return {
        "level1": {
            "level2": {
                "key1": "value1",
                "path_key": "/some/path",
            },
            "path_key2": "/some/other/path",
        },
        "list_with_none": [
            {"subkey1": "subvalue1"},
            "a_string",
        ],
        "another_key": "another_value",
    }


@pytest.fixture
def sample_dict():
    return {
        "level1": {
            "level2": {
                "key1": "value1",
                "key2": None,
                "_private_key": "private_value",
                "path_key": pathlib.Path("/some/path"),
            },
            "path_key2": pathlib.Path("/some/other/path"),
        },
        "list_with_none": [
            {"subkey1": "subvalue1", "subkey2": None},
            "a_string",
        ],
        "another_key": "another_value",
        "_private_key2": "private_value2",
        "root": pathlib.Path("/tmp/root"),
    }


class TestAddLevelsToDict:
    # TODO: Implement tests for add_levels_to_dict
    pass


class TestCleanDict:
    def test_clean_dict_titlecase(self, sample_dict, cleaned_sample_dict):
        cleaned_dict = abk.utils.dict_manipulation.clean_dict(
            sample_dict, keys_to_titlecase=True
        )

        assert cleaned_dict == abk.utils.dict_manipulation.dict_keys_to_titlecase(
            cleaned_sample_dict
        )

    def test_clean_dict_no_titlecase(self, sample_dict, cleaned_sample_dict):
        cleaned_dict = abk.utils.dict_manipulation.clean_dict(
            sample_dict, keys_to_titlecase=False
        )

        assert cleaned_dict == cleaned_sample_dict


class TestDeleteNoneFromDict:
    def test_delete_none_from_dict(self, sample_dict):
        cleaned_dict = abk.utils.dict_manipulation.delete_none_from_dict(sample_dict)

        assert "key2" not in cleaned_dict["level1"]["level2"]
        assert "subkey2" not in cleaned_dict["list_with_none"][1]


class TestDeletePrivateFieldsFromDict:
    def test_delete_private_fields_from_dict(self, sample_dict):
        cleaned_dict = abk.utils.dict_manipulation.delete_private_fields_from_dict(
            sample_dict
        )

        assert "_private_key" not in cleaned_dict["level1"]["level2"]
        assert "_private_key2" not in cleaned_dict


class TestDictKeysToTitlecase:
    def test_dict_keys_to_titlecase(self, sample_dict):
        titled_dict = abk.utils.dict_manipulation.dict_keys_to_titlecase(sample_dict)

        assert "Level1" in titled_dict
        assert "Level2" in titled_dict["Level1"]
        assert "Key1" in titled_dict["Level1"]["Level2"]
        assert "AnotherKey" in titled_dict


class TestDictPathsToStrings:
    def test_dict_paths_to_strings(self, sample_dict):
        stringified_dict = abk.utils.dict_manipulation.dict_paths_to_strings(
            sample_dict
        )

        assert isinstance(stringified_dict["level1"]["level2"]["path_key"], str)
        assert isinstance(stringified_dict["level1"]["path_key2"], str)
