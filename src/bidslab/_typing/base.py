"""Typing protocols and aliases for base classes."""

#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from bidslab.common.base import BaseAcquisition, BaseTask, Entity
    from bidslab.common.specs_misc import Run


#: Type alias for BaseAcquisition and its subclasses.
A = TypeVar("A", bound="BaseAcquisition")

#: Type alias for Entity and its subclasses.
E = TypeVar("E", bound="Entity")

#: Type alias for Run and its subclasses.
R = TypeVar("R", bound="Run")

#: Type alias for Task and its subclasses.
T = TypeVar("T", bound="BaseTask")


class Writable(Protocol):
    """
    Protocol for writable objects.

    A Writable is any object that can write itself to disk, therefore implements
    a `write` method.
    """

    def write(self, output_path: os.PathLike | str) -> None: ...


class PEntity(Writable, Protocol):
    """
    Protocol for Entity objects.

    A PEntity is any object that has an entity ID and name and is `Writable`.

    See Also
    --------
    Writable : Protocol
        Protocol for writable objects.
    :py:class:`bidslab.common.base.Entity`
        Base class for all entities in BIDSlab.
    """

    _entity_id: str
    _entity_name: str
