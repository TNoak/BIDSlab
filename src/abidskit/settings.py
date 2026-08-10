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
    Packages for dataset fetching.

    Attributes
    ----------
    DATALAD : str
        Use DataLad for dataset fetching.
    """

    DATALAD = ("dl",)


class PackageLoading(StrEnum):
    """
    Packages for data loading.

    Attributes
    ----------
    PANDAS : str
        Use Pandas for data loading.
    """

    PANDAS = ("pd",)
    NUMPY = ("np",)


PACKAGE_OPTIONS = ["DATASET_FETCHING_PACKAGE", "DATA_LOADING_PACKAGE"]


@dataclass(frozen=True)
class Settings:
    OVERRIDE_VALIDATION: bool = False
    SUPPORT_OLD_VERSIONS: bool = False
    IGNORE_VERSION: bool = False
    IGNORE_NOT_IMPLEMENTED: bool = False
    DATASET_FETCHING_PACKAGE: PackageFetching | None = None
    DATA_LOADING_PACKAGE: PackageLoading = PackageLoading.PANDAS


SETTINGS: Settings = Settings()


@contextmanager
def override_settings_values(
    settings: dict[str, bool | str] | os.PathLike,
) -> Generator[None, None, None]:
    """Temporarily set the value of a setting within a context."""
    global SETTINGS
    original_settings = SETTINGS.__dict__.copy()
    if isinstance(settings, os.PathLike):
        with pathlib.Path(settings).open("r", encoding="utf-8") as f:
            settings = json.load(f)

    assert isinstance(settings, dict)  # for mypy
    SETTINGS = Settings(**{**SETTINGS.__dict__, **settings})
    try:
        yield
    finally:
        SETTINGS = Settings(**{**SETTINGS.__dict__, **original_settings})


def set_settings_values(settings: dict[str, bool | str] | os.PathLike) -> None:
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


def get_settings_value(name: str) -> dict[str, bool]:
    """Get the current value of a setting."""
    global SETTINGS
    return SETTINGS.__dict__[name]


def save_settings_values(path: os.PathLike) -> None:
    """Save the current settings to a JSON file."""
    global SETTINGS
    with pathlib.Path(path).open("w", encoding="utf-8") as f:
        json.dump(SETTINGS.__dict__, f, indent=4)
