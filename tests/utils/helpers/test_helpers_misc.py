#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import pytest

import abidskit as abk
from abidskit.utils.exceptions import FieldNotValidError


class SampleClass:
    def __init__(self):
        self.attr1 = None
        self.attr2 = None


class TestSetClassAttributes:
    def test_set_class_attributes_from_dict(self):
        # Setup
        attr_dict = {"attr1": "value1", "attr2": 42}
        sample = SampleClass()

        # Test
        abk.utils.helpers.set_attr_from_dict(sample, attr_dict)

        assert sample.attr1 == "value1"
        assert sample.attr2 == 42

    def test_set_class_attributes_with_invalid_key(self):
        # Setup
        attr_dict = {"attr1": "value1", "attr3": "value3"}
        sample = SampleClass()

        # Test
        assert not hasattr(sample, "attr3")
        with pytest.raises(FieldNotValidError):
            abk.utils.helpers.set_attr_from_dict(sample, attr_dict)

        assert not hasattr(sample, "attr3")

        assert not hasattr(create_sample_class, "attr3")
