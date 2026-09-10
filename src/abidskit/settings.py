"""
Settings management for aBIDSkit.

This module provides functionality to manage and manipulate settings for the aBIDSkit
library. It includes a dataclass to hold the settings, context managers to temporarily
override settings, and functions to set, get, and save settings.
Settings can either be provided as a dictionary in code or loaded from a JSON file.
"""

#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import json
import os
import pathlib
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from typing import Generator


class PackageFetching(StrEnum):
    """
    Enumeration of available packages for dataset fetching.

    This enum defines the available external packages that can be used
    to fetch or download BIDS datasets.

    Attributes
    ----------
    DATALAD : str
        Use DataLad for dataset fetching. Value is "dl".

    Notes
    -----
    DataLad is a tool for managing data with Git and git-annex, providing
    efficient handling of large datasets.

    See Also
    --------
    PackageLoading : Enumeration for data loading packages.
    """

    DATALAD = ("dl",)


class PackageLoading(StrEnum):
    """
    Enumeration of available packages for data loading.

    This enum defines the available external packages that can be used
    to load or read data from BIDS datasets.

    Attributes
    ----------
    PANDAS : str
        Use Pandas for data loading. Value is "pd".
    NUMPY : str
        Use NumPy for data loading. Value is "np".

    Notes
    -----
    Pandas is suitable for tabular data (TSV files), while NumPy can be
    used for array-like data. Pandas is the default choice.

    See Also
    --------
    PackageFetching : Enumeration for dataset fetching packages.
    """

    PANDAS = ("pd",)
    NUMPY = ("np",)


PACKAGE_OPTIONS = ["DATASET_FETCHING_PACKAGE", "DATA_LOADING_PACKAGE"]


@dataclass(frozen=True)
class Settings:
    """
    Configuration settings for aBIDSkit.

    A frozen dataclass that holds all configuration settings for the aBIDSkit
    library. Settings control validation behavior, version support, and data
    handling packages used throughout the application.

    Attributes
    ----------
    OVERRIDE_VALIDATION : bool
        If True, override validation errors and warnings during data loading
        and processing. Default is False.
    SUPPORT_OLD_VERSIONS : bool
        If True, support features from older BIDS versions that may not
        conform to the latest specification. Default is False.
    IGNORE_VERSION : bool
        If True, ignore BIDS version mismatches when loading datasets.
        Default is False.
    IGNORE_NOT_IMPLEMENTED : bool
        If True, ignore NotImplementedError exceptions for incomplete features
        and continue processing. Default is False.
    DATASET_FETCHING_PACKAGE : PackageFetching | None
        The external package to use for fetching datasets. When None, no
        external fetching is used. Default is None.
    DATA_LOADING_PACKAGE : PackageLoading
        The package to use for loading and reading data files.
        Default is :py:attr:`PackageLoading.PANDAS`.

    Notes
    -----
    This class is immutable (frozen=True) for thread safety. To change
    settings, use :py:func:`set_settings_values` or the
    :py:func:`override_settings_values` context manager.

    See Also
    --------
    SETTINGS : The global instance of this class.
    set_settings_values : Function to permanently change settings.
    override_settings_values : Context manager for temporary setting overrides.
    """

    OVERRIDE_VALIDATION: bool = False
    SUPPORT_OLD_VERSIONS: bool = False
    IGNORE_VERSION: bool = False
    IGNORE_NOT_IMPLEMENTED: bool = False
    DATASET_FETCHING_PACKAGE: PackageFetching | None = None
    DATA_LOADING_PACKAGE: PackageLoading = PackageLoading.PANDAS


SETTINGS: Settings = Settings()
"""
Global settings instance for aBIDSkit.

See Also
--------
Settings : The settings dataclass.
"""


@contextmanager
def override_settings_values(
    settings: dict[str, bool | str] | os.PathLike,
) -> Generator[None, None, None]:
    """
    Temporarily override settings within a context block.

    This context manager temporarily replaces the global settings with new
    values. When exiting the context, the original settings are restored.
    This is useful for testing or running code with different configurations
    without permanently changing the application state.

    Parameters
    ----------
    settings : dict[str, bool | str] | os.PathLike
        Either a dictionary mapping setting names to values, or a path to a
        JSON file containing setting configurations.

    Yields
    ------
    None
        This is a context manager that yields control.

    Examples
    --------
    Temporarily override settings using a dictionary:

    >>> with override_settings_values({"OVERRIDE_VALIDATION": True}):
    ...     # Code here runs with OVERRIDE_VALIDATION set to True
    ...     pass
    >>> # Original settings restored here

    Load settings from a JSON file:

    >>> with override_settings_values("settings.json"):
    ...     # Code here runs with settings from the file
    ...     pass

    See Also
    --------
    set_settings_values : Permanently change settings.
    get_settings_value : Get a single setting value.
    """
    global SETTINGS
    original_settings = SETTINGS.__dict__.copy()
    if isinstance(settings, os.PathLike):
        with pathlib.Path(settings).open("r", encoding="utf-8") as f:
            settings = json.load(f)

    if isinstance(settings, dict):
        SETTINGS = Settings(**{**SETTINGS.__dict__, **settings})
    try:
        yield
    finally:
        SETTINGS = Settings(**{**SETTINGS.__dict__, **original_settings})


def set_settings_values(settings: dict[str, bool | str] | os.PathLike) -> None:
    """
    Permanently update global settings.

    This function permanently updates the global settings for the aBIDSkit
    library. Changes persist until explicitly modified or the application
    is restarted.

    Parameters
    ----------
    settings : dict[str, bool | str] | os.PathLike
        Either a dictionary mapping setting names to values, or a path to a
        JSON file containing setting configurations.

    Raises
    ------
    ValueError
        If an invalid value is provided for a package-related setting
        (DATASET_FETCHING_PACKAGE or DATA_LOADING_PACKAGE).

    Notes
    -----
    String values for package settings are automatically converted to the
    appropriate enum values (case-insensitive). Valid package values are:
    - DATASET_FETCHING_PACKAGE: "datalad" or "dl"
    - DATA_LOADING_PACKAGE: "pandas"/"pd" or "numpy"/"np"

    Examples
    --------
    Set settings using a dictionary:

    >>> set_settings_values({"OVERRIDE_VALIDATION": True})

    Load settings from a JSON file:

    >>> set_settings_values("settings.json")

    See Also
    --------
    override_settings_values : Context manager for temporary overrides.
    get_settings_value : Get a single setting value.
    save_settings_values : Save current settings to a file.
    """
    global SETTINGS
    if isinstance(settings, os.PathLike):
        with pathlib.Path(settings).open("r", encoding="utf-8") as f:
            settings = json.load(f)

    if isinstance(settings, dict):
        for setting_name in PACKAGE_OPTIONS:
            setting_value = settings.get(setting_name) or getattr(
                SETTINGS, setting_name
            )
            if isinstance(setting_value, str):
                match setting_name, setting_value.lower():
                    case "DATASET_FETCHING_PACKAGE", "datalad" | "dl":
                        setting_value = PackageFetching.DATALAD
                    case "DATA_LOADING_PACKAGE", "pandas" | "pd":
                        setting_value = PackageLoading.PANDAS
                    case "DATA_LOADING_PACKAGE", "numpy" | "np":
                        setting_value = PackageLoading.NUMPY
                    case _:
                        raise ValueError(
                            f"Invalid value '{setting_value}' for setting "
                            f"'{setting_name}'."
                        )

                settings[setting_name] = setting_value

        SETTINGS = Settings(**{**SETTINGS.__dict__, **settings})


def get_settings_value(name: str) -> str | bool | None:
    """
    Get the current value of a setting.

    Parameters
    ----------
    name : str
        The name of the setting to retrieve. Must be an attribute name
        from the :py:class:`Settings` class.

    Returns
    -------
    str | bool | None
        The current value of the setting, or None if the setting is not set.

    Raises
    ------
    KeyError
        If the setting name does not exist in the Settings class.

    Examples
    --------
    >>> value = get_settings_value("OVERRIDE_VALIDATION")
    >>> print(value)
    False

    See Also
    --------
    set_settings_values : Change a setting value.
    override_settings_values : Temporarily override a setting.
    """
    global SETTINGS
    return SETTINGS.__dict__[name]


def save_settings_values(path: os.PathLike) -> None:
    """
    Save current settings to a JSON file.

    Exports the current global settings to a JSON file, which can later
    be loaded using :py:func:`set_settings_values` or
    :py:func:`override_settings_values`.

    Parameters
    ----------
    path : os.PathLike
        The file system path where the settings JSON file should be saved.

    Notes
    -----
    The saved JSON file will contain all settings as they are currently
    configured. Enum values (PackageFetching, PackageLoading) are serialized
    to their string representation.

    Examples
    --------
    >>> save_settings_values("my_settings.json")
    >>> # Later, load these settings:
    >>> set_settings_values("my_settings.json")

    See Also
    --------
    set_settings_values : Load settings from a file.
    override_settings_values : Load settings temporarily from a file.
    """
    global SETTINGS
    with pathlib.Path(path).open("w", encoding="utf-8") as f:
        json.dump(SETTINGS.__dict__, f, indent=4)
