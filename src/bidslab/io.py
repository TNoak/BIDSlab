"""I/O functions for BIDS datasets.

This module provides functions to load and write BIDS datasets using the aBIDSkit
library. It wraps around the :py:class:`~abidskit.common.specs_dataset.Dataset` class
to provide easier access to loading and saving datasets via simple function calls.

"""

#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib

from bidslab.common.specs_dataset import Dataset


def load_dataset(path: os.PathLike | str, bids_version: str = "1.10.1") -> Dataset:
    """Load a BIDS dataset as a dataset object from the specified path on disk.

    This function loads a BIDS dataset located at the given file system path and
    returns it as a :py:class:`~abidskit.common.specs_dataset.Dataset` object. The
    dataset is validated against the specified BIDS version. This function wraps around
    the :py:class:`~abidskit.common.specs_dataset.Dataset` class and its
    :py:meth:`~abidskit.common.specs_dataset.Dataset.load` method
    from :py:mod:`~abidskit.common.specs_dataset`.

    Parameters
    ----------
    path : os.PathLike | str
        The file system path to the root of the BIDS dataset.
    bids_version : str, optional
        The BIDS version to validate against. Default is "1.10.1", the current latest
        stable version.

    Returns
    -------
    Dataset
        The loaded BIDS dataset as a :py:class:`~abidskit.common.specs_dataset.Dataset`
        object.

    """
    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)
    path = path.resolve()
    bids_dataset = Dataset(root=path, bids_version=bids_version)
    bids_dataset.load()

    return bids_dataset


def write_dataset(
    dataset: Dataset, output_path: os.PathLike | str, overwrite: bool = False
) -> None:
    """Write the dataset object as a BIDS dataset to the specified path on disk.

    This function writes the provided :py:class:`~bidslab.common.specs_dataset.Dataset`
    object to the specified file system path as a BIDS dataset. This function wraps
    around the :py:meth:`~bidslab.common.specs_dataset.Dataset.write` method from
    :py:mod:`~bidslab.common.specs_dataset`.

    Parameters
    ----------
    dataset : Dataset
        The BIDS dataset object to write to disk.
    output_path : os.PathLike | str
        The file system path where the BIDS dataset should be written.
    overwrite : bool, optional
        Whether to overwrite existing files at the output path. Default is False.

    """
    if not isinstance(output_path, pathlib.Path):
        output_path = pathlib.Path(output_path)

    dataset.write(output_path=output_path, overwrite=overwrite)
