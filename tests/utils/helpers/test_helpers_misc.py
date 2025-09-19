#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import pytest

from abidskit.utils.exceptions import FieldNotValidError
from abidskit.utils.helpers import set_attr_from_dict


class SampleClass:
    def __init__(self, **kwargs):
        self.attr1 = None
        self.attr2 = None


@pytest.fixture
def create_sample_class():
    return SampleClass()


class TestSetClassAttributes:
    def test_set_class_attributes_from_dict(self, create_sample_class):
        # Setup
        attr_dict = {"attr1": "value1", "attr2": 42}

        # Test
        set_attr_from_dict(create_sample_class, attr_dict)

        assert create_sample_class.attr1 == "value1"
        assert create_sample_class.attr2 == 42

    def test_set_class_attributes_with_invalid_key(self, create_sample_class):
        # Setup
        attr_dict = {"attr1": "value1", "attr3": "value3"}

        # Test
        assert not hasattr(create_sample_class, "attr3")
        with pytest.raises(FieldNotValidError):
            set_attr_from_dict(create_sample_class, attr_dict)

        assert not hasattr(create_sample_class, "attr3")
