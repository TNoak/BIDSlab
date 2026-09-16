"""
I/O functions for BIDS datasets.

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
    """
    Load a BIDS dataset from disk as a Dataset object.

    This function loads a complete BIDS dataset from the specified file system path,
    parses all dataset structure and metadata, and returns a fully-populated
    :py:class:`~abidskit.common.specs_dataset.Dataset` object. The dataset is validated
    against the specified BIDS version to ensure compliance.

    The function provides a convenient high-level interface to the
    :py:class:`~abidskit.common.specs_dataset.Dataset` class and its
    :py:meth:`~abidskit.common.specs_dataset.Dataset.load` method. It automatically
    handles path normalization and dataset initialization.

    Parameters
    ----------
    path : os.PathLike | str
        The file system path to the root directory of the BIDS dataset.
        Must point to a valid BIDS dataset with a ``dataset_description.json`` file.
    bids_version : str, optional
        The BIDS specification version to validate the dataset against.
        Default is "1.10.1" (current latest stable version).

    Returns
    -------
    Dataset
        The loaded BIDS dataset as a :py:class:`~abidskit.common.specs_dataset.Dataset`
        object. Contains all subjects, sessions, datatypes, tasks, and metadata
        loaded from the dataset directory.

    Raises
    ------
    FileNotFoundError
        If the dataset path does not exist or is not a valid BIDS dataset.
    ValueError
        If the dataset does not contain a valid ``dataset_description.json``.
    Exception
        If the dataset fails validation against the specified BIDS version.

    See Also
    --------
    write_dataset : Save a dataset object back to disk.
    Dataset.load : The underlying load method used internally.
    Dataset : The main dataset class.

    Notes
    -----
    This function performs a full dataset load including:
    - Parsing the dataset description and metadata
    - Scanning all subject and session directories
    - Loading datatype definitions and task metadata
    - Indexing all data files and associated sidecars
    - Validating BIDS compliance

    For large datasets, especially in remote places, this operation may take some time.
    Consider the dataset size and available memory before loading very large BIDS
    datasets. Data is nevertheless loaded lazily.

    Examples
    --------
    >>> from abidskit import load_dataset
    >>> dataset = load_dataset("/path/to/bids/dataset")
    >>> print(f"Dataset: {dataset.name}")
    >>> print(f"Number of subjects: {len(dataset.participants)}")

    Load a dataset and access motion data:

    >>> for participant in dataset.participants:
    ...     for session in participant.sessions:
    ...         for datatype in session.datatypes:
    ...             if datatype.datatype_name == "motion":
    ...                 print(
    ...                     f"Motion data for {participant.participant_id}/" +
    ...                     f"{session.session_id}"
    ...                 )
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
    """
    Write a Dataset object to disk as a BIDS dataset.

    This function serializes a :py:class:`~abidskit.common.specs_dataset.Dataset` object
    to the file system, creating a valid BIDS-compliant dataset directory structure.
    It handles all metadata files, sidecar JSON files, and data file organization
    according to BIDS standards.

    The function provides a convenient high-level interface to the
    :py:class:`~abidskit.common.specs_dataset.Dataset` class and its
    :py:meth:`~abidskit.common.specs_dataset.Dataset.write` method.

    Parameters
    ----------
    dataset : Dataset
        The :py:class:`~abidskit.common.specs_dataset.Dataset` object to write to disk.
        Must be a valid Dataset with at least the required metadata fields.
    output_path : os.PathLike | str
        The file system path where the BIDS dataset should be written.
        This will be created if it does not exist.
    overwrite : bool, optional
        Whether to overwrite existing files if output_path already contains data.
        Default is False, which raises an error if files would be overwritten.

    Raises
    ------
    FileExistsError
        If output_path exists and overwrite is False.
    ValueError
        If the dataset is invalid or missing required metadata.
    OSError
        If there are file system errors during writing.

    See Also
    --------
    load_dataset : Load a dataset from disk.
    Dataset.write : The underlying write method used internally.
    Dataset : The main dataset class.

    Notes
    -----
    This function writes:
    - Dataset description (``dataset_description.json``)
    - README and CHANGES files
    - Phenotypic data (``participants.tsv``, ``participants.json``)
    - All subject/session/datatype/task/acquisition hierarchies
    - Data files and associated JSON sidecars
    - Task-specific metadata files

    The dataset must have valid metadata before writing. Use overwrite=True with
    caution, as it will replace existing files in the output directory.

    Examples
    --------
    >>> from abidskit import load_dataset, write_dataset
    >>> dataset = load_dataset("/path/to/original/dataset")
    >>> # Modify dataset...
    >>> write_dataset(dataset, "/path/to/output/dataset")

    Save with overwrite enabled (use with caution):

    >>> write_dataset(dataset, "/path/to/output/dataset", overwrite=True)
    """
    if not isinstance(output_path, pathlib.Path):
        output_path = pathlib.Path(output_path)

    dataset.write(output_path=output_path, overwrite=overwrite)
