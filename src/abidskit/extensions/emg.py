#  Copyright (c) 2026 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
# 
#  SPDX-License-Identifier: BSD-3-Clause
#
#  SPDX-License-Identifier: BSD-3-Clause

import json
import pathlib
import re
from dataclasses import dataclass
from typing import Any, MutableMapping, MutableSequence, Sequence

from abidskit.common.specs_misc import (
    Column,
    Filter,
    Hardware,
    Institution,
    Recording,
)
from abidskit.utils.exceptions import (
    FieldEntryNotValidError,
    FieldMissingError,
)
from abidskit.utils.helpers import set_attr_from_dict
from abidskit.utils.string_manipulation import to_snakecase

EMG_CHANNEL_TYPE_ALLOWED_FIELD_ENTRIES = {
    "ECG",
    "EMG",
    "EOG",
    "HEOG",
    "LATENCY",
    "MISC",
    "REF",
    "SYSCLOCK",
    "TRIG",
    "VEOG",
}


@dataclass(slots=True)
class EMGHardware(Hardware):
    electrode_manufacturer: str | None = None
    electrode_manufacturers_model_name: str | None = None


@dataclass(slots=True)
class EMGCoordinateSystem:
    name: str
    emg_coordinate_system: str
    emg_coordinate_units: str
    emg_coordinate_system_description: str | None = None
    parent_coordinate_system: "EMGCoordinateSystem | None" = None
    anchor_coordinates: Sequence[int | float] | None = None
    anchor_electrode: str | None = None

    def __post_init__(self):
        if self.emg_coordinate_system == "Other" and not self.emg_coordinate_system_description:
            raise FieldMissingError("Field `EMGCoordinateSystemDescription` must be present if field `EMGCoordinateSystem` is 'Other'")
        if self.parent_coordinate_system:
            if not self.anchor_coordinates:
                raise FieldMissingError("Field `AnchorCoordinates` must be present if field `ParentCoordinateSystem` is present")
            if not self.anchor_electrode:
                raise FieldMissingError("Field `AnchorElectrode` must be present if field `ParentCoordinateSystem` is present")

    def __repr__(self) -> str:
        return f"<EMGCoordinateSystem name={self.name}>"

    def __hash__(self) -> int:
        return id(self)


class EMGChannel:
    def __init__(
        self,
        name: str,
        type: str,  # noqa: A002
        units: str,
        **kwargs: Any,
    ):
        self.name: str = name
        self._type: str = type
        self.units: str = units
        self.description: str | None = None
        self.sampling_frequency: int | float | None = None
        self.signal_electrode: str | None = None
        self.reference: str | None = None
        self.group: str | int | float | None = None
        self.target_muscle: str | None = None
        self.placement_scheme: str | None = None
        self.placement_description: str | None = None
        self.interelectrode_distance: int | float | None = None
        self.low_cutoff: int | float | None = None
        self.high_cutoff: int | float | None = None
        self.notch: str | None = None
        self.status: str | None = None
        self.status_description: str | None = None
        self.columns: Sequence[Column] | None = None

        set_attr_from_dict(self, kwargs)

    def __repr__(self) -> str:
        return f"<EMGChannel name={self.name}>"

    @property
    def type(self) -> str | None:
        return self._type

    @type.setter  # noqa: A003
    def type(self, value: str) -> None:
        if value not in EMG_CHANNEL_TYPE_ALLOWED_FIELD_ENTRIES:
            raise FieldEntryNotValidError(
                f"Field `Type` must be one "
                f"of {EMG_CHANNEL_TYPE_ALLOWED_FIELD_ENTRIES}"
            )
        self._type = value


class EMGElectrode:
    def __init__(
            self,
            name: str,
            x: int | float,
            y: int | float,
            **kwargs: Any,
    ):
        self.name: str = name
        self.x: int | float = x
        self.y: int | float = y
        self.z: int | float | None = None
        self.coordinate_system: EMGCoordinateSystem | None = None
        self.type: str | None = None
        self.material: str | None = None
        self.impedance: int | float | None = None
        self.group: str | int | float | None = None
        self.columns: Sequence[Column] | None = None

        set_attr_from_dict(self, kwargs)


class EMGRecording(Recording):
    def __init__(
        self,
        recording_id: str,
        sampling_frequency: int | float,
        placement_scheme: str,
        emg_reference: str,
        power_line_frequency: int | float | str,
        recording_type: str,
        software_filters: MutableMapping[str, Filter] | str,
        **kwargs: Any,
    ):
        self.recording_id: str = recording_id

        self.sampling_frequency: int | float = sampling_frequency
        self.emg_placement_scheme: str = placement_scheme
        if self.emg_placement_scheme != "Other":
            self.emg_placement_scheme_description: str | None = None
        else:
            try:
                self.emg_placement_scheme_description = kwargs.pop("EMGPlacementSchemeDescription")
            except KeyError:
                raise FieldMissingError("Field `EMGPlacementSchemeDescription` must be present if field `EMGPlacementScheme` is 'Other'") from None
        self.emg_reference: str = emg_reference
        self.power_line_frequency: int | float | str = power_line_frequency
        self.recording_type: str = recording_type
        self.software_filters: MutableMapping[str, Filter] | str = software_filters
        self.emg_channel_count: int | None = None
        self.hardware_filters: MutableMapping[str, Filter] | str | None = None
        self.recording_duration: int | float | None = None
        self.electrode_material: str | None = None
        self.electrode_type: str | None = None
        self.emg_ground: str | None = None
        self.epoch_length: int | float | None = None
        self.gain: int | float | None = None
        self.interelectrode_distance: int | float | None = None
        self.preamplification: int | float | None = None
        self.skin_preparation: str | None = None
        self.subject_artefact_description: str | None = None
        self.trigger_channel_count: int | None = None

        self._hardware: EMGHardware | None = None
        self._institution: Institution | None = None

        self._electrodes: MutableSequence[EMGElectrode] | None = None
        self._channels: MutableSequence[EMGChannel] | None = None

        set_attr_from_dict(self, kwargs)

    @property
    def hardware(self) -> EMGHardware | None:
        return self._hardware

    @hardware.setter
    def hardware(self, value: dict | EMGHardware) -> None:
        if isinstance(value, dict):
            hardware_data = {}
            for k, v in value.items():
                hardware_data[to_snakecase(k)] = v
            self._hardware = EMGHardware(**hardware_data)
        elif isinstance(value, EMGHardware):
            self._hardware = value
        else:
            raise TypeError("Field `Hardware` must be a EMGHardware object")

    @property
    def institution(self) -> Institution | None:
        return self._institution

    @institution.setter
    def institution(self, value: dict | Institution) -> None:
        if isinstance(value, dict):
            institution_data = {}
            for k, v in value.items():
                institution_data[to_snakecase(k)] = v
            self._institution = Institution(**institution_data)
        elif isinstance(value, Institution):
            self._institution = value
        else:
            raise TypeError("Field `Institution` must be a Institution object")


def parse_emg_json_sidecar(sidecar_path: pathlib.Path) -> dict:
    with sidecar_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        task_description = {}
        hardware_description = {}
        institution_description = {}
        emg_description = {}
        for key, value in data.items():
            if re.match(r"^Task[A-Z].*|^Instructions", key):
                task_description[key] = value
            elif re.match(
                    r"^Device[A-Z].*|^(Electrode)?Manufacturer.*|^SoftwareVersions", key
            ):
                hardware_description[key] = value
            elif re.match(r"^Institution.*", key):
                institution_description[key] = value
            else:
                emg_description[key] = value

        return {
            "task": task_description,
            "hardware": hardware_description,
            "institution": institution_description,
            "emg": emg_description,
        }
