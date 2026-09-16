"""Filters to apply to BIDS Datasets."""

#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

from collections.abc import Sequence
from copy import deepcopy

from bidslab.common.specs_dataset import Dataset


def filter_participants(dataset: Dataset, participant_ids: Sequence[str]) -> Dataset:
    """
    Return a Dataset that only contains the given participants.

    Parameters
    ----------
    dataset : Dataset
        Dataset that the filter will be applied to.
    participant_ids : Sequence[str]
        Sequence of participant_ids that the resulting Dataset should include.

    Returns
    -------
    Dataset
        Dataset with the applied filter.
    """
    output_dataset = deepcopy(dataset)
    for key in dataset.participants:
        if key not in participant_ids:
            output_dataset.participants.pop(key)

    return output_dataset


def filter_sessions(dataset: Dataset, session_ids: Sequence[str]) -> Dataset:
    """
    Return a Dataset that only contains the given sessions.

    Parameters
    ----------
    dataset : Dataset
        Dataset that the filter will be applied to.
    session_ids : Sequence[str]
        Sequence of session_ids that the resulting Dataset should include.

    Returns
    -------
    Dataset
        Dataset with the applied filter.
    """
    output_dataset = deepcopy(dataset)
    for pkey, participant in dataset.participants.items():
        for key in participant.sessions:
            if key not in session_ids:
                output_dataset.participants[pkey].sessions.pop(key)

    return output_dataset


def filter_datatypes(dataset: Dataset, datatype_names: Sequence[str]) -> Dataset:
    """
    Return a Dataset that only contains the given datatype.

    Parameters
    ----------
    dataset : Dataset
        Dataset that the filter will be applied to.
    datatype_names : Sequence[str]
        Sequence of datatype names that the resulting Dataset should include.

    Returns
    -------
    Dataset
        Dataset with the applied filter.
    """
    output_dataset = deepcopy(dataset)
    for pkey, participant in dataset.participants.items():
        for skey, session in participant.sessions.items():
            for key in session.datatypes:
                if key not in datatype_names:
                    output_dataset.participants[pkey].sessions[skey].datatypes.pop(key)

    return output_dataset


def filter_dataset(
    dataset: Dataset,
    participant_ids: Sequence[str] | None = None,
    session_ids: Sequence[str] | None = None,
    datatype_names: Sequence[str] | None = None,
) -> Dataset:
    """
    Return a Dataset that only contains the given parts.

    Parameters
    ----------
    dataset : Dataset
        Dataset that the filter will be applied to.
    participant_ids : Sequence[str] | None
        Sequence of participant_ids that the resulting Dataset should include.
    session_ids : Sequence[str] | None
        Sequence of session_ids that the resulting Dataset should include.
    datatype_names : Sequence[str] | None
        Sequence of datatype names that the resulting Dataset should include.

    Returns
    -------
    Dataset
        Dataset with the applied filters.
    """
    output_dataset = deepcopy(dataset)
    if participant_ids is not None:
        output_dataset = filter_participants(
            dataset=dataset, participant_ids=participant_ids
        )
    if session_ids is not None:
        output_dataset = filter_sessions(
            dataset=output_dataset, session_ids=session_ids
        )
    if datatype_names is not None:
        output_dataset = filter_datatypes(
            dataset=output_dataset, datatype_names=datatype_names
        )
    return output_dataset
