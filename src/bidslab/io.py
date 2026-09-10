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
