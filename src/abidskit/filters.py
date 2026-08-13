#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

from copy import deepcopy
from typing import Sequence

from abidskit.common.specs_description import Dataset


def filter_participants(dataset: Dataset, participant_ids: Sequence[str]) -> Dataset:
    output_dataset = deepcopy(dataset)
    for key in dataset.participants:
        if key not in participant_ids:
            output_dataset.participants.pop(key)

    return output_dataset


def filter_sessions(dataset: Dataset, session_ids: Sequence[str]) -> Dataset:
    output_dataset = deepcopy(dataset)
    for pkey, participant in dataset.participants.items():
        for key in participant.sessions:
            if key not in session_ids:
                output_dataset.participants[pkey].sessions.pop(key)

    return output_dataset


def filter_datatypes(dataset: Dataset, datatype_names: Sequence[str]) -> Dataset:
    output_dataset = deepcopy(dataset)
    for pkey, participant in dataset.participants.items():
        for skey, session in participant.sessions.items():
            for key in session.datatypes:
                if key not in datatype_names:
                    output_dataset.participants[pkey].sessions[skey].datatypes.pop(key)

    return output_dataset


def filter_dataset(
    dataset,
    participant_ids: Sequence[str] | None = None,
    session_ids: Sequence[str] | None = None,
    datatype_names: Sequence[str] | None = None,
) -> Dataset:
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
