#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import pytest
from mimesis import Development

from abidskit.common.specs_description import Dataset
from abidskit.settings import override_settings_values
from abidskit.utils.checks import check_if_valid_uri, check_version
from abidskit.utils.exceptions import (
    InvalidURIError,
    VersionMismatchError,
    VersionMismatchWarning,
)

VALID_URIS = [
    "doi:10.18112/openneuro.ds000001.v1.0.0",
    "bids::sub-01/fmap/sub-01_dir-AP_epi.nii.gz",
    "bids:ds000001:sub-02/anat/sub-02_T1w.nii.gz",
    "bids:myderivatives:sub-03/func/sub-03_task-rest_space-MNI152_bold.nii.gz",
    "s3://dicoms/studies/correlates",
    "https://openneuro.org/datasets/ds000114/versions/1.0.1",
    "file:///data/phantoms",
]

INVALID_URIS = [
    "10.18112/openneuro.ds000001.v1.0.0",
    "not_a_uri",
]


class TestVersion:
    def test_same_version(self, tmp_root):
        dev = Development()
        vs = dev.version()
        ds = Dataset(tmp_root, bids_version=vs)
        assert ds.bids_version == vs
        check_version(ds, vs)

    def test_different_version_warning(self, tmp_root):
        dev = Development()
        ds = Dataset(tmp_root, bids_version=dev.version())
        vs = dev.version()
        assert ds.bids_version != vs
        with override_settings_values({"IGNORE_VERSION": True}):
            with pytest.warns(VersionMismatchWarning):
                check_version(ds, vs)

    def test_different_version_error(self, tmp_root):
        dev = Development()
        ds = Dataset(tmp_root, bids_version=dev.version())
        vs = dev.version()
        assert ds.bids_version != vs
        with pytest.raises(VersionMismatchError):
            check_version(ds, vs)


class TestURI:
    @pytest.mark.parametrize("uri", VALID_URIS)
    def test_valid_uri(self, uri):
        check_if_valid_uri(uri)

    @pytest.mark.parametrize("uri", INVALID_URIS)
    def test_invalid_uri(self, uri):
        with pytest.raises(InvalidURIError):
            check_if_valid_uri(uri)
