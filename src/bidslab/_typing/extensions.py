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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bidslab.extensions.eeg import EEGChannel, EEGElectrode
    from bidslab.extensions.emg import EMGChannel, EMGElectrode
    from bidslab.extensions.ieeg import IEEGChannel, IEEGElectrode
    from bidslab.extensions.motion import MotionChannel


type EEGChannelType = "EEGChannel"
type EEGElectrodeType = "EEGElectrode"
type EMGChannelType = "EMGChannel"
type EMGElectrodeType = "EMGElectrode"
type IEEGChannelType = "IEEGChannel"
type IEEGElectrodeType = "IEEGElectrode"
type MotionChannelType = "MotionChannel"
