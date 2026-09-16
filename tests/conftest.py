#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import itertools
import random

import pytest
from mimesis import Development

import bidslab as abk


class FixtureParameterNotSupportedError(Exception):
    pass


def _permutate_dict(data):
    # Source - https://stackoverflow.com/a/61557885
    # Posted by Thierry Lathuille
    # Retrieved 2025-11-25, License - CC BY-SA 4.0

    product_values = itertools.product(*data.values())
    return [dict(zip(data.keys(), values, strict=False)) for values in product_values]


@pytest.fixture(scope="module")
def tmp_root(tmp_path_factory):
    return tmp_path_factory.mktemp("bids_dataset")


@pytest.fixture
def good_file_structure(tmp_root, request):
    files = [
        "README" + request.param,
        "CITATION.cff",
        "dataset_description.json",
        "participants.tsv",
        "sub-01/anat/sub-01_T1w.nii.gz",
        "sourcedata/sub-01/anat/sub-01_T1w.nii.gz",
        "code/script.py",
        "stimuli/image.png",
        "CHANGES",
        "LICENSE" + request.param,
    ]

    make_files(tmp_root, files)

    yield tmp_root

    delete_files(tmp_root, files)


@pytest.fixture
def bad_file_structure(tmp_root, request):
    files = request.param

    make_files(tmp_root, files)

    yield tmp_root

    delete_files(tmp_root, files)


@pytest.fixture
def test_dataset(tmp_root):
    return abk.common.specs_dataset.Dataset(
        tmp_root, name="Test Dataset", bids_version=Development().version()
    )


def make_files(tmp_root, files):
    for file in files:
        file_path = tmp_root / file
        file_path.parent.mkdir(exist_ok=True, parents=True)
        file_path.touch()


def delete_files(tmp_root, files):
    for file in files:
        file_path = tmp_root / file
        if file_path.exists():
            file_path.unlink()


def make_mock_files(tmp_root, files):
    file_paths = [tmp_root / file for file in files]
    random.shuffle(file_paths)
    return file_paths
