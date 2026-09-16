"""
Typing protocols and aliases for extensions.

This module provides type variable definitions for BIDS extension-specific classes
in BIDSlab. These type definitions enable static type checking, enhance IDE support,
and ensure type safety when working with extension entities such as Motion and EMG.
"""

#  Copyright (c) 2026 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from bidslab.extensions.emg import EMGChannel, EMGElectrode
    from bidslab.extensions.motion import MotionChannel

#: TypeVar bound to :py:class:`bidslab.extensions.motion.MotionChannel`
#: and its subclasses.
MC = TypeVar("MC", bound="MotionChannel")

#: TypeVar bound to :py:class:`bidslab.extensions.emg.EMGChannel` and its subclasses.
EC = TypeVar("EC", bound="EMGChannel")

#: TypeVar bound to :py:class:`bidslab.extensions.emg.EMGElectrode` and its subclasses.
EE = TypeVar("EE", bound="EMGElectrode")
