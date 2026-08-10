#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import re

import pytest

from abidskit.utils.string_manipulation import (
    remove_special_characters,
    to_snakecase,
    to_titlecase,
)

TITLES = [
    ("One_small_sentence", "OneSmallSentence"),
    ("Another Example Here", "AnotherExampleHere"),
    ("ALL CAPS TITLE", "AllCapsTitle"),
    ("mixed_Case Title", "MixedCaseTitle"),
    ("  leading and trailing spaces  ", "LeadingAndTrailingSpaces"),
    ("BidS version", "BIDSVersion"),
    ("A doi", "ADOI"),
    ("Patient id", "PatientID"),
    ("hed Hierarchical Event Descriptors", "HEDHierarchicalEventDescriptors"),
    ("This is a url link", "ThisIsAURLLink"),
    ("We can use a rrid", "WeCanUseARRID"),
    ("An accelerometer accel", "AnAccelerometerACCEL"),
    ("Angular acceleration angaccel", "AngularAccelerationANGACCEL"),
    ("Gyroscope gyro", "GyroscopeGYRO"),
    ("Magnetometer magn", "MagnetometerMAGN"),
    ("Joint angle jntang", "JointAngleJNTANG"),
    ("Orientation ornt", "OrientationORNT"),
    ("Position pos", "PositionPOS"),
    ("Velocity vel", "VelocityVEL"),
    ("Miscellaneous misc", "MiscellaneousMISC"),
    ("Latency", "LATENCY"),
    ("This is an URL and an uri", "ThisIsAnURLAndAnURI"),
    ("The term url should be possible as well", "TheTermURLShouldBePossibleAsWell"),
]

SNAKES = [
    ("OneSmallSentence", "one_small_sentence"),
    ("Another Example Here", "another_example_here"),
    ("ALL CAPS TITLE", "all_caps_title"),
    ("mixed_Case Title", "mixed_case_title"),
    ("  leading and trailing spaces  ", "leading_and_trailing_spaces"),
    ("BIDSVersion", "bids_version"),
    ("ADOI", "a_doi"),
    ("PatientID", "patient_id"),
    ("HEDHierarchicalEventDescriptors", "hed_hierarchical_event_descriptors"),
    ("ThisIsAURLLink", "this_is_a_url_link"),
    ("WeCanUseARRID", "we_can_use_a_rrid"),
    ("AnAccelerometerACCEL", "an_accelerometer_accel"),
    ("AngularAccelerationANGACCEL", "angular_acceleration_angaccel"),
    ("GyroscopeGYRO", "gyroscope_gyro"),
    ("MagnetometerMAGN", "magnetometer_magn"),
    ("JointAngleJNTANG", "joint_angle_jntang"),
    ("OrientationORNT", "orientation_ornt"),
    ("PositionPOS", "position_pos"),
    ("VelocityVEL", "velocity_vel"),
    ("MiscellaneousMISC", "miscellaneous_misc"),
    ("LATENCY", "latency"),
    ("ThisIsAnURLAndAnURI", "this_is_an_url_and_an_uri"),
    ("TheTermURLShouldBePossibleAsWell", "the_term_url_should_be_possible_as_well"),
]


class TestCaseConversion:
    @pytest.mark.parametrize(("case", "result"), TITLES)
    def test_to_titlecase(self, case, result):
        title_case = to_titlecase(case)
        assert title_case == result

    @pytest.mark.parametrize(("case", "result"), SNAKES)
    def test_to_snakecase(self, case, result):
        snake_case = to_snakecase(case)
        assert snake_case == result


def test_remove_special_characters():
    removed = remove_special_characters(
        "This! is@ a# $test% ^string& *with(36)special_+ -characters: {}[]|;='<>,.?/`~"
    )
    assert removed == "This+is+a+test+string+with+36+special+characters"
    assert re.match(r"^[a-zA-Z0-9+]*$", removed)
