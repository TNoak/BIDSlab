#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

from warnings import warn

import pytest

import abidskit as abk
from abidskit.utils.exceptions import FieldNotValidError, TopLevelEntityNotLinkedWarning


class SampleClass:
    def __init__(self, attr1=None, attr2=None):
        self.attr1 = attr1
        self.attr2 = attr2


class SampleClassWarnTopLevel:
    def __init__(self, attr1=None):
        self.attr1 = attr1

        warn("Top level entity not linked", TopLevelEntityNotLinkedWarning)


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

    def test_set_class_attributes_missing_top_level_entity(self):
        # Setup
        attr_dict = {"attr1": "value1"}
        with pytest.warns(TopLevelEntityNotLinkedWarning):
            sample = SampleClassWarnTopLevel()

        # Test
        abk.utils.helpers.set_attr_from_dict(sample, attr_dict)  # No warning here
        assert sample.attr1 == "value1"
