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


class TestAddEntityToList:
    def test_add_entity_to_list(self):
        # Setup
        entity_list = []
        entity = SampleClass

        # Test
        abk.utils.helpers.add_entity_to_list(entity_list, entity)
        assert type(entity_list[0]) is SampleClass

    def test_add_entity_to_list_with_nonempty_list(self):
        # Setup
        entity_list = [SampleClass()]
        entity = SampleClass

        # Test
        abk.utils.helpers.add_entity_to_list(entity_list, entity)
        assert type(entity_list[1]) is SampleClass
        assert len(entity_list) == 2

    def test_add_entity_to_list_multiple_times(self):
        # Setup
        entity_list = []
        entity = SampleClass

        # Test
        abk.utils.helpers.add_entity_to_list(entity_list, entity)
        abk.utils.helpers.add_entity_to_list(entity_list, entity)
        assert type(entity_list[0]) is SampleClass
        assert type(entity_list[1]) is SampleClass
        assert len(entity_list) == 2

    def test_add_entity_to_list_with_arguments(self):
        # Setup
        entity_list = []
        entity = SampleClass
        args = {"attr1": "value1"}

        # Test
        abk.utils.helpers.add_entity_to_list(entity_list, entity, **args)
        assert type(entity_list[0]) is SampleClass
        assert entity_list[0].attr1 == "value1"

    def test_add_entity_to_list_with_invalid_entity(self):
        # Setup
        entity_list = []
        entity = "NotAClass"

        # Test
        with pytest.raises(TypeError):
            abk.utils.helpers.add_entity_to_list(entity_list, entity)
        assert len(entity_list) == 0
