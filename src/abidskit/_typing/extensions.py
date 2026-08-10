"""Typing protocols and aliases for extensions."""

#  Copyright (c) 2026 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from abidskit.extensions.emg import EMGChannel, EMGElectrode
    from abidskit.extensions.motion import MotionChannel

#: Type alias for MotionChannel.
MC = TypeVar("MC", bound="MotionChannel")

#: Type alias for EMGChannel.
EC = TypeVar("EC", bound="EMGChannel")

#: Type alias for EMGElectrode.
EE = TypeVar("EE", bound="EMGElectrode")
