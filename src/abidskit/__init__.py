"""
aBIDSkit is a Python package for working with BIDS datasets.

This tool implements functions for loading and creating BIDS (Brain Imaging Data
Structure) datasets.
"""

#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

__version__ = "0.2.0"
__author__ = "Lukas Behammer"

__all__ = [
    "get_version",
    "load_dataset",
]

from .io import load_dataset


def get_version():
    """
    Return the version of the aBIDSkit package.

    Returns
    -------
    str
        The version string of the package.
    """
    return __version__
