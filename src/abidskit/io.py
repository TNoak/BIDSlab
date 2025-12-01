#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib

from abidskit.common.specs_description import Dataset


def load_dataset(path: os.PathLike | str, bids_version: str = "1.10.1") -> Dataset:
    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    bids_dataset = Dataset(root=path, bids_version=bids_version)
    bids_dataset.load()

    return bids_dataset
