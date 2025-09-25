#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib


class Run:
    def __init__(self, base_path: os.PathLike | str, run_id: str):
        self.run_id = run_id
        # TODO: make sure that run_id is "run-<int>"

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._acquisition = None

        self._recordings = None
        self._events = None

    # @property
    # def acquisition(self):
    #     return self._acquisition

    # @acquisition.setter
    # def acquisition(self, value):
    #     self._acquisition = value

    # @property
    # def recordings(self):
    #     raise NotImplementedError

    # @recordings.setter
    # def recordings(self, value: Iterable[dict] | Iterable[Recording]):
    #     raise NotImplementedError

    # @property
    # def events(self):
    #     raise NotImplementedError

    # @events.setter
    # # TODO: implement
    # def events(self, value: Iterable[dict] | Iterable[Event]):
    #     raise NotImplementedError
