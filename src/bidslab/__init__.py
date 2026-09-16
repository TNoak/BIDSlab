# numpydoc ignore=SS02
"""
BIDSlab is a Python package for working with BIDS datasets.

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
    "override_settings",
    "save_settings",
    "update_settings",
    "write_dataset",
]

from .io import load_dataset, write_dataset
from .settings import override_settings_values as override_settings
from .settings import save_settings_values as save_settings
from .settings import set_settings_values as update_settings


def get_version():
    """
    Return the version of the BIDSlab package.

    Returns
    -------
    str
        The version string of the package.
    """
    return __version__
