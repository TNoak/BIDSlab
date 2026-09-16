"""String manipulation utilities."""

#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import re

SHORT_FORMS = {
    "id": "ID",
    "uri": "URI",
    "url": "URL",
    "doi": "DOI",
    "bids": "BIDS",
    "rrid": "RRID",
    "accel": "ACCEL",
    "angaccel": "ANGACCEL",
    "gyro": "GYRO",
    "jntang": "JNTANG",
    "latency": "LATENCY",
    "magn": "MAGN",
    "misc": "MISC",
    "ornt": "ORNT",
    "pos": "POS",
    "vel": "VEL",
    "hed": "HED",
    "emg": "EMG",
}


def to_titlecase(string: str) -> str:
    """
    Convert a string to TitleCase, preserving known short forms.

    Parameters
    ----------
    string : str
        The input string to convert.

    Returns
    -------
    str
        The converted TitleCase string.
    """
    parts = re.split(r"[_ ]", string)
    parts = [
        SHORT_FORMS[part.lower()] if part.lower() in SHORT_FORMS else part.title()
        for part in parts
    ]
    return "".join(parts)


def to_snakecase(string: str) -> str:
    """
    Convert a string to snake_case, preserving known short forms.

    Parameters
    ----------
    string : str
        The input string to convert.

    Returns
    -------
    str
        The converted snake_case string.
    """
    for _, value in SHORT_FORMS.items():
        if value == "ACCEL":
            # avoid matching ANGACCEL
            string = re.sub("(?<!ANG)(ACCEL)", f" {value} ", string)
        elif value == "ID":
            # avoid matching RRID or BIDS
            # TODO: make this more robust
            string = re.sub("(?<!RR)(ID)(?!S)", f" {value} ", string)
        else:
            string = re.sub(value, f" {value} ", string)
    string = re.sub(r"[_ ]", "_", string.strip())
    string = re.sub(r"([a-z])([A-Z])", r"\1_\2", string)
    return string.lower()


def remove_special_characters(string: str) -> str:
    """
    Remove special characters from a string, replacing them with '+'.

    Parameters
    ----------
    string : str
        The input string to process.

    Returns
    -------
    str
        The processed string with special characters replaced by '+'.
    """
    string = re.sub(r"[^a-zA-Z0-9]", " ", string)
    return re.sub(r"\s+", "+", string).strip("+")
