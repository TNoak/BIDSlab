#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import pathlib

import pytest

import bidslab as abk
from bidslab.utils.exceptions import FileTypeUnsupportedWarning
from tests.conftest import delete_files, make_files

PATHS = [
    (
        pathlib.Path("C:/Users/user/Documents/Projects/BIDS_dataset"),
        pathlib.Path(
            "C:/Users/user/Documents/Projects/BIDS_dataset/sub-01/ses-01/task-walking"
        ),
        [
            pathlib.Path("C:/Users/user/Documents/Projects/BIDS_dataset/sub-01/ses-01"),
            pathlib.Path("C:/Users/user/Documents/Projects/BIDS_dataset/sub-01"),
        ],
    ),
    (
        pathlib.Path("/home/user/Documents/Projects/BIDS_dataset"),
        pathlib.Path(
            "/home/user/Documents/Projects/BIDS_dataset/sub-01/ses-01/task-walking"
        ),
        [
            pathlib.Path("/home/user/Documents/Projects/BIDS_dataset/sub-01/ses-01"),
            pathlib.Path("/home/user/Documents/Projects/BIDS_dataset/sub-01"),
        ],
    ),
    (
        pathlib.Path("C:/BIDS_dataset"),
        pathlib.Path("C:/BIDS_dataset/sub-01/ses-01/task-walking"),
        [
            pathlib.Path("C:/BIDS_dataset/sub-01/ses-01"),
            pathlib.Path("C:/BIDS_dataset/sub-01"),
        ],
    ),
    (
        pathlib.Path("/BIDS_dataset"),
        pathlib.Path("/BIDS_dataset/sub-01/ses-01/task-walking"),
        [
            pathlib.Path("/BIDS_dataset/sub-01/ses-01"),
            pathlib.Path("/BIDS_dataset/sub-01"),
        ],
    ),
    (
        pathlib.Path("C:/ses-01/sub-01/BIDS_dataset"),
        pathlib.Path("C:/ses-01/sub-01/BIDS_dataset/sub-01/ses-01/task-walking"),
        [
            pathlib.Path("C:/ses-01/sub-01/BIDS_dataset/sub-01/ses-01"),
            pathlib.Path("C:/ses-01/sub-01/BIDS_dataset/sub-01"),
        ],
    ),
    (
        pathlib.Path("/ses-01/sub-01/BIDS_dataset"),
        pathlib.Path("/ses-01/sub-01/BIDS_dataset/sub-01/ses-01/task-walking"),
        [
            pathlib.Path("/ses-01/sub-01/BIDS_dataset/sub-01/ses-01"),
            pathlib.Path("/ses-01/sub-01/BIDS_dataset/sub-01"),
        ],
    ),
]

MATCHES = [
    ("task", {"task": "walking"}),
    ("sub", {"sub": "01"}),
    ("ses", {"ses": "01"}),
    ("run", {"run": "01"}),
    ("acq", {}),
    ("bold", {}),
    ("sub|ses", {"sub": "01", "ses": "01"}),
    ("sub | ses", {"sub": "01", "ses": "01"}),
]


class TestGetRootFiles:
    @pytest.mark.parametrize("good_file_structure", [""], indirect=True)
    def test_root_files_paths(self, test_dataset, good_file_structure):
        assert test_dataset.changes_path is None
        assert test_dataset.sourcedata_path is None
        assert test_dataset.code_path is None
        assert test_dataset.stimuli_path is None

        abk.utils.helpers.get_root_files(test_dataset)

        assert test_dataset.changes_path == good_file_structure / "CHANGES"
        assert test_dataset.sourcedata_path == good_file_structure / "sourcedata"
        assert test_dataset.code_path == good_file_structure / "code"
        assert test_dataset.stimuli_path == good_file_structure / "stimuli"

    @pytest.mark.parametrize(
        "bad_file_structure",
        [["dataset_description.json", "README.md", "README.rst"]],
        indirect=True,
    )
    def test_root_files_readme_multiple(self, test_dataset, bad_file_structure):
        with pytest.raises(abk.utils.exceptions.MultipleFilesFoundError):
            abk.utils.helpers.get_root_files(test_dataset)


class TestGetTsvJsonFiles:
    def test_tsv_json_files(self, tmp_root):
        # Setup
        files = ["example_scans.tsv", "example_scans.json"]
        make_files(tmp_root, files)

        # Test
        tsv_path, json_path = abk.utils.helpers.get_tsv_json_files(tmp_root, "*_scans")
        assert tsv_path == tmp_root / "example_scans.tsv"
        assert json_path == tmp_root / "example_scans.json"

        # Teardown
        delete_files(tmp_root, files)

    def test_tsv_json_files_wrong_filename(self, tmp_root):
        # Setup
        files = ["example_scans.tsv", "example_scans.json"]
        make_files(tmp_root, files)

        # Test
        tsv_path, json_path = abk.utils.helpers.get_tsv_json_files(
            tmp_root, "*wrong_name*"
        )
        assert tsv_path is None
        assert json_path is None

        # Teardown
        delete_files(tmp_root, files)

    def test_tsv_json_files_filetype_unsupported(self, tmp_root):
        # Setup
        files = ["example_scans.csv"]
        make_files(tmp_root, files)

        # Test
        with pytest.warns(FileTypeUnsupportedWarning):
            tsv_path, json_path = abk.utils.helpers.get_tsv_json_files(
                tmp_root, "*_scans"
            )
        assert tsv_path is None
        assert json_path is None

        # Teardown
        delete_files(tmp_root, files)

    def test_tsv_json_files_multiple_tsv(self, tmp_root):
        # Setup
        files = ["example_scans.tsv", "second_scans.tsv"]
        make_files(tmp_root, files)

        # Test
        with pytest.warns(abk.utils.exceptions.MultipleFilesFoundWarning):
            tsv_path, json_path = abk.utils.helpers.get_tsv_json_files(
                tmp_root, "*_scans"
            )
        assert tsv_path == tmp_root / "example_scans.tsv"
        assert json_path is None

        # Teardown
        delete_files(tmp_root, files)

    def test_tsv_json_files_multiple_json(self, tmp_root):
        # Setup
        files = ["example_scans.json", "second_scans.json"]
        make_files(tmp_root, files)

        # Test
        with pytest.warns(abk.utils.exceptions.MultipleFilesFoundWarning):
            tsv_path, json_path = abk.utils.helpers.get_tsv_json_files(
                tmp_root, "*_scans"
            )
        assert tsv_path is None
        assert (
            json_path == tmp_root / "example_scans.json"
            or tmp_root / "second_scans.json"
        )

        # Teardown
        delete_files(tmp_root, files)


@pytest.mark.parametrize("paths", PATHS)
def test_get_matching_subpaths(paths):
    # Setup
    root_path, search_path, expected = paths

    # Test
    result = abk.utils.helpers.get_matching_subpaths(
        path=search_path,
        matches=["sub-*", "ses-*"],
        root=root_path,
    )
    assert result == expected


@pytest.mark.parametrize("entity", MATCHES)
def test_get_entity_from_file(entity):
    # Setup
    file_path = pathlib.Path(
        "C:/Users/user/Documents/Projects/sub-02/ses-03/acq-01/BIDS_dataset/sub-01/ses-01/sub-01_ses-01_task-walking_run-01_bold.nii.gz"
    )

    # Test
    result = abk.utils.helpers.get_entity_from_file(file_path, entity[0])
    assert result == entity[1]
