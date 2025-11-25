#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from abidskit.common.base import BaseAcquisition, Entity, Run
    from abidskit.extensions.motion import MotionChannel


A = TypeVar("A", bound="BaseAcquisition")
MC = TypeVar("MC", bound="MotionChannel")
E = TypeVar("E", bound="Entity")
R = TypeVar("R", bound="Run")


class Writable(Protocol):
    def write(self, output_path: os.PathLike | str) -> None: ...


class PEntity(Writable, Protocol):
    _entity_id: str
    _entity_name: str
