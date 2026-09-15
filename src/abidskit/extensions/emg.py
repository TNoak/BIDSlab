"""
EMG extension models for BIDS electromyography datasets.

This module implements EMG-specific hardware, coordinate system, channel,
electrode, recording, acquisition, and task models together with helper
functions for parsing EMG sidecars and tabular metadata.
"""

#  Copyright (c) 2026 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import json
import os
import pathlib
import re
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from warnings import warn

import pandas as pd

from abidskit.common.base import BaseAcquisition, BaseTask
from abidskit.common.specs_misc import (
    Column,
    Filter,
    Hardware,
    Institution,
    Recording,
    Run,
)
from abidskit.settings import get_settings_value
from abidskit.utils.dict_manipulation import ManipulateKeysOption, clean_dict
from abidskit.utils.exceptions import (
    FieldEntryNotValidError,
    FieldMissingError,
    FileNotFoundWarning,
    TopLevelEntityNotLinkedWarning,
)
from abidskit.utils.helpers import (
    add_object_to_sequence,
    get_edf_json_files,
    get_entity_from_file,
    get_tsv_json_files,
    load_edf_data,
    parse_descriptive_tsv,
    parse_json_sidecar,
    set_attr_from_dict,
)
from abidskit.utils.string_manipulation import to_snakecase

if TYPE_CHECKING:
    from abidskit.common import Datatype

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
    """
    Extend generic hardware metadata with EMG electrode manufacturer fields.

    Attributes
    ----------
    electrode_manufacturer : str | None, optional
        Manufacturer of the surface, fine-wire, or high-density electrodes used
        during acquisition.
    electrode_manufacturers_model_name : str | None, optional
        Manufacturer-reported model name or catalog number for the electrodes.

    See Also
    --------
    :py:class:`EMGRecording`
        Recording-level container that links hardware and channel metadata.

    Notes
    -----
    Store electrode-specific vendor information here when the amplifier and the
    electrodes come from different manufacturers. This complements the inherited
    :py:class:`~abidskit.common.specs_misc.Hardware` fields describing the main
    recording system.

    Examples
    --------
    Record both amplifier and electrode vendor information

    >>> hardware = EMGHardware(
    ...     manufacturer="Delsys",
    ...     manufacturers_model_name="Trigno Avanti",
    ...     electrode_manufacturer="Delsys",
    ...     electrode_manufacturers_model_name="DE-2.1",
    ... )
    """

    electrode_manufacturer: str | None = None
    electrode_manufacturers_model_name: str | None = None


@dataclass(slots=True)
class EMGCoordinateSystem:
    """
    Represent an EMG electrode coordinate system.

    Attributes
    ----------
    name : str
        Local identifier used to reference the coordinate system.
    emg_coordinate_system : str
        Coordinate-system keyword defined by the BIDS standard, for example
        ``CapTrak``, ``EEGLAB`` or ``Other``.
    emg_coordinate_units : str
        Spatial units used for electrode coordinates, typically ``mm`` or ``cm``.
    emg_coordinate_system_description : str | None, optional
        Required explanatory text when ``emg_coordinate_system`` is ``Other``.
    parent_coordinate_system : EMGCoordinateSystem | None, optional
        Parent system used for hierarchical localization, such as registering a
        muscle grid to a body-segment frame.
    anchor_coordinates : Sequence[int | float] | None, optional
        Coordinates of the anchor point in the parent system.
    anchor_electrode : str | None, optional
        Electrode name used as anchor when nesting coordinate systems.

    Raises
    ------
    FieldMissingError
        If a required description or anchoring field is omitted.

    See Also
    --------
    :py:class:`EMGElectrode`
        Electrode definitions that use this coordinate system.
    :py:class:`EMGRecording`
        Recording-level container that aggregates electrodes and channels.

    Notes
    -----
    The EMG extension requires additional descriptive fields when the coordinate
    system is ``Other`` or linked to a parent coordinate system. This is useful
    for documenting electrode grids on anatomical landmarks, custom templates,
    or digitized skin coordinates.

    Examples
    --------
    Define a digitized anatomical coordinate system

    >>> coords = EMGCoordinateSystem(
    ...     name="forearm-grid",
    ...     emg_coordinate_system="Other",
    ...     emg_coordinate_units="mm",
    ...     emg_coordinate_system_description=(
    ...         "2D grid aligned with the radius-ulna axis on the dominant forearm."
    ...     ),
    ... )

    Register a child grid to a segment-level parent frame

    >>> EMGCoordinateSystem(
    ...     name="biceps-grid",
    ...     emg_coordinate_system="Other",
    ...     emg_coordinate_units="mm",
    ...     emg_coordinate_system_description="High-density grid placed over biceps brachii.",
    ...     parent_coordinate_system=coords,
    ...     anchor_coordinates=[25, 10, 0],
    ...     anchor_electrode="E01",
    ... )
    """

    name: str
    emg_coordinate_system: str
    emg_coordinate_units: str
    emg_coordinate_system_description: str | None = None
    parent_coordinate_system: "EMGCoordinateSystem | None" = None
    anchor_coordinates: Sequence[int | float] | None = None
    anchor_electrode: str | None = None

    def __post_init__(self):
        """Validate coordinate system configuration."""
        if (
            self.emg_coordinate_system == "Other"
            and not self.emg_coordinate_system_description
        ):
            raise FieldMissingError(
                "Field `EMGCoordinateSystemDescription` must be present if field "
                "`EMGCoordinateSystem` is 'Other'"
            )
        if self.parent_coordinate_system:
            if not self.anchor_coordinates:
                raise FieldMissingError(
                    "Field `AnchorCoordinates` must be present if field "
                    "`ParentCoordinateSystem` is present"
                )
            if not self.anchor_electrode:
                raise FieldMissingError(
                    "Field `AnchorElectrode` must be present if field "
                    "`ParentCoordinateSystem` is present"
                )

    def __repr__(self) -> str:
        """Return a string representation of the EMGCoordinateSystem object."""
        return f"<EMGCoordinateSystem name={self.name}>"

    def __hash__(self) -> int:
        """Return a hash of the coordinate system."""
        return id(self)


class EMGChannel:
    """
    Represent one EMG channel definition from ``*_channels.tsv``.

    Parameters
    ----------
    name : str
        Channel name used in tabular metadata and renamed sample data columns.
    type : str
        BIDS channel type. Typical values are ``EMG`` for muscle activity,
        ``REF`` for reference leads, ``TRIG`` for trigger inputs, ``ECG`` or
        ``EOG`` for physiological monitoring, and ``MISC`` for auxiliary signals.
    units : str
        Measurement unit such as ``uV``, ``mV``, or ``V``.
    **kwargs
        Optional metadata describing electrode pairing, target muscle, filters,
        channel grouping, placement scheme, and status information.

    Raises
    ------
    FieldEntryNotValidError
        If ``type`` is not allowed by the EMG extension.

    See Also
    --------
    :py:class:`EMGRecording`
        Recording object that owns channel definitions and sample data.
    :py:class:`EMGElectrode`
        Electrode definitions referenced by ``signal_electrode`` or ``reference``.

    Notes
    -----
    Use channel metadata to document whether a signal comes from a bipolar pair,
    monopolar sensor, reference channel, or synchronization input. Placement and
    muscle annotations help downstream processing pipelines organize channels.

    Examples
    --------
    Create a bipolar muscle channel and a trigger channel

    >>> emg = EMGChannel(
    ...     name="EMG_FCR",
    ...     type="EMG",
    ...     units="uV",
    ...     target_muscle="flexor carpi radialis",
    ...     signal_electrode="E01",
    ...     reference="E02",
    ... )
    >>> trig = EMGChannel(name="Trigger", type="TRIG", units="V")
    """

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
        """Return a string representation of the EMGChannel object."""
        return f"<EMGChannel name={self.name}>"

    @property
    def type(self) -> str | None:
        # numpydoc ignore=RT01
        """Return the validated EMG channel type."""
        return self._type

    @type.setter  # noqa: A003
    def type(self, value: str) -> None:
        # numpydoc ignore=GL08
        if value not in EMG_CHANNEL_TYPE_ALLOWED_FIELD_ENTRIES:
            raise FieldEntryNotValidError(
                f"Field `Type` must be one of {EMG_CHANNEL_TYPE_ALLOWED_FIELD_ENTRIES}"
            )
        self._type = value


class EMGElectrode:
    """
    Represent one EMG electrode definition from ``*_electrodes.tsv``.

    Parameters
    ----------
    name : str
        Electrode label used in electrode tables and channel references.
    x : int | float
        X coordinate of the electrode center in the associated coordinate system.
    y : int | float
        Y coordinate of the electrode center in the associated coordinate system.
    **kwargs
        Optional metadata including ``z`` coordinates, electrode type, material,
        impedance, grouping, and linked :py:class:`EMGCoordinateSystem`.

    See Also
    --------
    :py:class:`EMGCoordinateSystem`
        Coordinate system used for electrode localization.
    :py:class:`EMGChannel`
        Channel metadata that can reference the electrode by name.

    Notes
    -----
    Use electrodes to document sensor placement on the skin, in a grid, or in a
    fine-wire configuration. Coordinate and impedance metadata are especially
    important for reproducible placement descriptions and quality control.

    Examples
    --------
    Describe a surface electrode

    >>> electrode = EMGElectrode(
    ...     name="E01",
    ...     x=12.5,
    ...     y=31.0,
    ...     z=0.0,
    ...     type="surface",
    ...     material="Ag/AgCl",
    ...     impedance=4.2,
    ... )
    """

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

    def __repr__(self) -> str:
        """Return a string representation of the EMGElectrode object."""
        return f"<EMGElectrode name={self.name}>"


class EMGRecording(Recording):
    """
    Represent one EMG recording and its associated metadata/data.

    Parameters
    ----------
    base_path : os.PathLike | str
        Directory containing the recording files.
    recording_id : str
        BIDS recording label, usually ``recording-<label>``.
    sampling_frequency : int | float
        Sampling rate of the recording in hertz.
    emg_placement_scheme : str
        Placement scheme identifier, for example ``SENIAM`` or ``Other``.
    emg_reference : str
        Description of the reference strategy, such as a dedicated reference
        electrode, common average, or differential pair.
    power_line_frequency : int | float | str
        Mains frequency affecting the recording, typically ``50`` or ``60``.
    recording_type : str
        Recording mode, such as continuous or epoched acquisition.
    software_filters : MutableMapping[str, Filter] | str
        Software filtering description stored in the EMG sidecar.
    **kwargs
        Optional recording metadata, linked hardware or institution objects,
        channels, electrodes, coordinate systems, and inherited sidecar content.

    Raises
    ------
    TypeError
        If ``_description`` is supplied with the wrong type.
    FieldMissingError
        If ``emg_placement_scheme`` is ``Other`` without an accompanying
        description.

    See Also
    --------
    :py:class:`EMGRun`
        Parent run containing one or more recordings.
    :py:class:`EMGChannel`
        Channel metadata used to label data columns.
    :py:class:`EMGElectrode`
        Electrode metadata associated with the recording.

    Notes
    -----
    :py:class:`EMGRecording` combines setup metadata with lazily loaded sample
    data. Use it to document electrode placement scheme, referencing, filtering,
    and recording-specific quality annotations before accessing :py:attr:`data`.

    Examples
    --------
    Create a recording with standard setup metadata

    >>> recording = EMGRecording(
    ...     base_path="sub-01/ses-01/emg",
    ...     recording_id="recording-rest",
    ...     sampling_frequency=2000,
    ...     emg_placement_scheme="SENIAM",
    ...     emg_reference="Bipolar differential",
    ...     power_line_frequency=50,
    ...     recording_type="continuous",
    ...     software_filters="None",
    ... )

    Access metadata and sample data together

    >>> muscles = [channel.target_muscle for channel in recording.channels or []]
    >>> samples = recording.data
    """

    def __init__(
        self,
        base_path: os.PathLike | str,
        recording_id: str,
        sampling_frequency: int | float,
        emg_placement_scheme: str,
        emg_reference: str,
        power_line_frequency: int | float | str,
        recording_type: str,
        software_filters: MutableMapping[str, Filter] | str,
        **kwargs: Any,
    ):
        # TODO: filters should be filter objects
        description = kwargs.pop("_description", None)
        if description is not None and not isinstance(description, MutableMapping):
            raise TypeError(
                "Parameter type for argument `_description` must be MutableMapping"
            )
        self._description: MutableMapping | None = description

        super().__init__(
            base_path=base_path,
            recording_id=recording_id,
            sampling_frequency=sampling_frequency,
        )

        self.emg_placement_scheme: str = emg_placement_scheme
        if self.emg_placement_scheme != "Other":
            self.emg_placement_scheme_description: str | None = None
        else:
            try:
                self.emg_placement_scheme_description = kwargs.pop(
                    "emg_placement_scheme_description"
                )
            except KeyError:
                raise FieldMissingError(
                    "Field `EMGPlacementSchemeDescription` must be present if field "
                    "`EMGPlacementScheme` is 'Other'"
                ) from None
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
        self._coordinate_system: EMGCoordinateSystem | None = None

        self._run: "EMGRun | None" = None

        # Try to set attributes from arguments
        set_attr_from_dict(self, kwargs)

        self._update_description()

        # Update values from self._description
        if self._description:
            emg_description = self._description.pop("emg", {})
            _ = self._description.pop("task", None)
            set_attr_from_dict(self, {**self._description, **emg_description})

    def __repr__(self) -> str:
        """Return a string representation of the EMGRecording entity."""
        return f"<EMGRecording id={self.recording_id}>"

    @property
    def hardware(self) -> EMGHardware | None:
        # numpydoc ignore=RT01
        """Return hardware metadata linked to the EMG recording."""
        return self._hardware

    @hardware.setter
    def hardware(self, value: Mapping | EMGHardware) -> None:
        # numpydoc ignore=GL08
        if isinstance(value, Mapping):
            hardware_data = {}
            for k, v in value.items():
                hardware_data[to_snakecase(k)] = v
            self._hardware = EMGHardware(**hardware_data)
        elif isinstance(value, EMGHardware):
            self._hardware = value
        else:
            raise TypeError("Field `Hardware` must be an EMGHardware object")

    @property
    def institution(self) -> Institution | None:
        # numpydoc ignore=RT01
        """Return institution metadata linked to the EMG recording."""
        return self._institution

    @institution.setter
    def institution(self, value: Mapping | Institution) -> None:
        # numpydoc ignore=GL08
        if isinstance(value, Mapping):
            institution_data = {}
            for k, v in value.items():
                institution_data[to_snakecase(k)] = v
            self._institution = Institution(**institution_data)
        elif isinstance(value, Institution):
            self._institution = value
        else:
            raise TypeError("Field `Institution` must be an Institution object")

    @property
    def channels(self) -> MutableSequence[EMGChannel] | None:
        # numpydoc ignore=RT01
        """Return channel definitions associated with the recording."""
        return self._channels

    @channels.setter
    def channels(self, value: MutableSequence[Mapping | EMGChannel]) -> None:
        # numpydoc ignore=GL08
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, Mapping) for entry in value):
                self._channels = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._channels.append(EMGChannel(**entry))
            elif all(isinstance(entry, EMGChannel) for entry in value):
                self._channels = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Channels` must be a list of EMGChannel object")

    @property
    def electrodes(self) -> MutableSequence[EMGElectrode] | None:
        # numpydoc ignore=RT01
        """Return electrode definitions associated with the recording."""
        return self._electrodes

    @electrodes.setter
    def electrodes(self, value: MutableSequence[Mapping | EMGElectrode]) -> None:
        # numpydoc ignore=GL08
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, Mapping) for entry in value):
                self._electrodes = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._electrodes.append(EMGElectrode(**entry))
            elif all(isinstance(e, EMGElectrode) for e in value):
                self._electrodes = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Electrodes` must be a list of EMGElectrodes object")

    # @property
    # def coordinate_system(self) -> EMGCoordinateSystem | None:
    #     return self._coordinate_system
    #
    # @coordinate_system.setter
    # def coordinate_system(self, value: EMGCoordinateSystem) -> None:
    #     self._coordinate_system = value

    @property
    def data(self):
        # numpydoc ignore=RT01
        """Load or return cached EMG sample data."""
        if self._data is None:
            file_name = f"*{self.run.acquisition.task.task_id}*"
            file_name += (
                f"_{self.run.acquisition.acquisition_id}"
                if len(self.run.acquisition.task.acquisitions) > 1
                else ""
            )
            file_name += (
                f"_{self.run.run_id}" if len(self.run.acquisition.runs) > 1 else ""
            )
            file_name += f"_{self.recording_id}" if len(self.run.recordings) > 1 else ""
            edf_path, _ = get_edf_json_files(
                self.root,
                file_name + "_emg",
            )
            data_frame = load_edf_data(path=edf_path)
            column_names = {}
            for channel_number, channel in enumerate(self.channels):
                column_names[channel_number] = channel.name
            data_frame.rename(columns=column_names, inplace=True)

            self._data = data_frame

        return self._data

    @data.setter
    def data(self, value: pd.DataFrame) -> None:
        # numpydoc ignore=GL08
        self._data = value

    def _update_description(self) -> None:
        """Update inherited description metadata for the recording."""
        file_name = f"*_{self.recording_id}_"
        _update_description_data(self, file_name)


class EMGRun(Run):
    """
    Represent an EMG run containing one or more recordings.

    Parameters
    ----------
    base_path : os.PathLike | str
        Directory containing run-level EMG files.
    run_id : int
        Numeric run identifier used to resolve ``run-<index>`` entities.
    **kwargs : Any
        Optional acquisition link and inherited description metadata.

    Raises
    ------
    TypeError
        If ``_description`` is not a mutable mapping.

    See Also
    --------
    :py:class:`EMGAcquisition`
        Parent acquisition that groups runs.
    :py:class:`EMGRecording`
        Recording objects exposed through :py:attr:`recordings`.

    Notes
    -----
    Runs group one or more :py:class:`EMGRecording` objects. Recordings are
    discovered from filenames, and a default ``recording-00`` object is created
    when files omit the recording entity.

    Examples
    --------
    Access recordings and inspect loaded signals

    >>> run = acquisition.runs[0]
    >>> first_recording = run.recordings[0]
    >>> data = first_recording.data

    Iterate over all recording labels discovered in the run

    >>> for recording in run.recordings:
    ...     print(recording.recording_id, len(recording.channels or []))
    """

    def __init__(self, base_path: os.PathLike | str, run_id: int, **kwargs: Any):
        description = kwargs.pop("_description", {})
        if not isinstance(description, MutableMapping):
            raise TypeError(
                "Parameter type for argument `_description` must be MutableMapping"
            )
        self._description: MutableMapping = description

        super().__init__(base_path=base_path, run_id=run_id, **kwargs)

        self._recordings: MutableSequence[EMGRecording] | None = None

        self._update_description()

    # def __repr__(self) -> str:
    #     return f"<Run id=run-{self.run_id}>"

    @property
    def recordings(self) -> MutableSequence[EMGRecording] | None:
        # numpydoc ignore=RT01
        """Get recordings belonging to the run."""
        if not self._recordings:
            # TODO make this more elegant
            file_name = f"*{self.acquisition.task.task_id}"
            file_name += (
                f"_{self.acquisition.acquisition_id}"
                if len(self.acquisition.task.acquisitions) > 1
                else ""
            )
            file_name += f"_{self.run_id}" if len(self.acquisition.runs) > 1 else ""

            self._recordings = []
            files = self.root.iterdir()
            recording_labels = set()
            for file in files:
                try:
                    recording_labels.add(
                        get_entity_from_file(
                            file,
                            "recording",
                        )["recording"]
                    )
                except KeyError:
                    continue

            # values in self._description get passed forward as fallback / to follow the
            # inheritance principle of BIDS but will be updated downstream
            for recording_label in recording_labels:
                self._recordings.append(
                    EMGRecording(
                        recording_id="recording-" + recording_label,
                        base_path=self.root,
                        run=self,
                        hardware=self._description.get("hardware", None),
                        institution=self._description.get("institution", None),
                        channels=get_emg_channels(
                            *get_tsv_json_files(
                                self.root,
                                file_name + f"_recording-{recording_label}_channels",
                            )
                        ),
                        electrodes=self._description.get("electrodes", None),
                        **self._description.get("emg", None),
                    )
                )

            # If no recordings are found, add a default one
            if not self._recordings:
                self._recordings.append(
                    EMGRecording(
                        recording_id="recording-00",
                        base_path=self.root,
                        run=self,
                        hardware=self._description.get("hardware", None),
                        institution=self._description.get("institution", None),
                        channels=get_emg_channels(
                            *get_tsv_json_files(
                                self.root,
                                file_name + "_channels",
                            )
                        ),
                        electrodes=self._description.get("electrodes", None),
                        **self._description.get("emg", None),
                    )
                )

        return self._recordings

    @recordings.setter
    def recordings(self, value: MutableSequence[MutableMapping | EMGRecording]) -> None:
        # numpydoc ignore=GL08
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, MutableMapping) for entry in value):
                self._recordings = []
                for entry in value:
                    assert isinstance(entry, MutableMapping)  # for mypy
                    self._recordings.append(
                        EMGRecording(
                            base_path=self.root,
                            run=self,
                            **entry,
                        )
                    )
            elif all(isinstance(entry, EMGRecording) for entry in value):
                self._recordings = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError(
                "Field `Recordings` must be a list of EMGRecordings objects"
            )

    def _update_description(self) -> None:
        """Refresh inherited description metadata for the run."""
        file_name = f"*_run-{self.run_id}_*_"
        _update_description_data(self, file_name)


class EMGAcquisition(BaseAcquisition):
    """
    Represent an EMG acquisition beneath a task.

    Parameters
    ----------
    base_path : os.PathLike | str
        Directory containing acquisition-level EMG files.
    acquisition_id : str
        BIDS acquisition label, usually ``acq-<label>``.
    **kwargs : Any
        Optional task link, inherited sidecar description metadata, and
        preconstructed runs.

    Raises
    ------
    TypeError
        If ``_description`` is not a mutable mapping.

    See Also
    --------
    :py:class:`EMGTask`
        Parent task containing the acquisition.
    :py:class:`EMGRun`
        Run objects created under the acquisition.

    Notes
    -----
    The acquisition acts as the bridge between task-level metadata and run-level
    recordings. It refreshes inherited description blocks and lazily constructs
    :py:class:`EMGRun` objects from files in the acquisition directory.

    Examples
    --------
    Create or load an acquisition and enumerate runs

    >>> acquisition = EMGAcquisition(
    ...     base_path="sub-01/ses-01/emg",
    ...     acquisition_id="acq-grip",
    ... )
    >>> run_ids = [run.run_id for run in acquisition.runs]
    """

    def __init__(
        self,
        base_path: os.PathLike | str,
        acquisition_id: str,
        **kwargs: Any,
    ):
        description = kwargs.pop("_description", {})
        if not isinstance(description, MutableMapping):
            raise TypeError(
                "Parameter type for argument `_description` must be MutableMapping"
            )
        self._description: MutableMapping = description

        super().__init__(base_path=base_path, acquisition_id=acquisition_id)

        self._task: "EMGTask | None" = None

        self._update_description()

        set_attr_from_dict(self, kwargs)

    @property
    def runs(self) -> MutableSequence[EMGRun]:
        # numpydoc ignore=RT01
        """Return runs associated with the acquisition."""
        if not self._runs:
            self._runs = []
            files = self.root.iterdir()
            run_ids = set()
            for file in files:
                try:
                    run_ids.add(
                        get_entity_from_file(
                            file,
                            "run",
                        )["run"]
                    )
                except KeyError:
                    continue
            for run_id in run_ids:
                run_id_int = int(run_id.split("-")[1])
                self._runs.append(
                    EMGRun(
                        run_id=run_id_int,
                        base_path=self.root,
                        acquisition=self,
                        _description=self._description,
                    )
                )

            # If no runs are found, add a default one
            if not self._runs:
                self._runs.append(
                    EMGRun(
                        run_id=0,
                        base_path=self.root,
                        acquisition=self,
                        _description=self._description,
                    )
                )

        return self._runs

    @runs.setter
    def runs(self, value: MutableSequence[int | EMGRun]) -> None:
        # numpydoc ignore=GL08
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, int) for entry in value):
                self._runs = []
                for entry in value:
                    assert isinstance(entry, int)  # for mypy
                    self._runs.append(
                        EMGRun(
                            run_id=entry,
                            base_path=self.root,
                            acquisition=self,
                            _description=self._description,
                        )
                    )
            elif all(isinstance(v, EMGRun) for v in value):
                self._runs = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Runs` must be a list of EMGRun objects")

    @property
    def task(self) -> "EMGTask | None":
        # numpydoc ignore=RT01
        """Get the parent :py:class:`EMGTask` linked to the acquisition."""
        if self._task:
            return self._task

        warn(
            "Acquisition is not linked to a EMGTask object.",
            TopLevelEntityNotLinkedWarning,
        )
        return self._task

    @task.setter
    def task(self, value: "EMGTask") -> None:
        # numpydoc ignore=GL08
        self._task = value

    def _update_description(self) -> None:
        """Refresh inherited description metadata for the acquisition."""
        file_name = f"*_{self.acquisition_id}_*_"
        _update_description_data(self, file_name)


class EMGTask(BaseTask):
    """
    Represent a BIDS EMG task composed of acquisitions.

    Parameters
    ----------
    base_path : os.PathLike | str
        Root directory containing task-specific EMG files.
    task_name : str
        BIDS task label used to resolve files such as ``task-<label>``.
    **kwargs : str | Datatype | MutableSequence | MutableMapping
        Optional task metadata, datatype information, inherited description
        blocks, and acquisition objects.

    Raises
    ------
    TypeError
        If ``_description`` is not a mutable mapping.

    See Also
    --------
    :py:class:`EMGAcquisition`
        Acquisition objects belonging to the task.
    :py:meth:`write`
        Task-level write entry point for future EMG serialization support.

    Notes
    -----
    EMG tasks typically describe paradigms such as rest, maximal voluntary
    contraction, gait, or grasping. The :py:attr:`acquisitions` property scans
    for acquisition entities and creates :py:class:`EMGAcquisition` objects with
    inherited metadata for downstream run and recording discovery.

    Examples
    --------
    Load an EMG task and inspect its hierarchy::

    >>> task = EMGTask(base_path="sub-01/ses-01/emg", task_name="grip")
    >>> for acquisition in task.acquisitions:
    ...     print(acquisition.acquisition_id, len(acquisition.runs))
    """

    def __init__(
        self,
        base_path: os.PathLike | str,
        task_name: str,
        **kwargs: "str | Datatype | MutableSequence | MutableMapping",
    ) -> None:
        description = kwargs.pop("_description", {})
        if not isinstance(description, MutableMapping):
            raise TypeError(
                "Parameter type for argument `_description` must be MutableMapping"
            )
        self._description: MutableMapping = description

        super().__init__(base_path=base_path, task_name=task_name, **kwargs)

        self._acquisitions: MutableSequence[EMGAcquisition] | None = None

    @property
    def acquisitions(self) -> MutableSequence[EMGAcquisition]:
        # numpydoc ignore=RT01
        """Return acquisitions discovered for the EMG task."""
        if not self._acquisitions:
            self._acquisitions = []
            files = self.root.iterdir()
            acquisition_labels = set()
            for file in files:
                try:
                    acquisition_labels.add(
                        get_entity_from_file(
                            file,
                            "acq",
                        )["acq"]
                    )
                except KeyError:
                    continue
            for acquisition_label in acquisition_labels:
                self._acquisitions.append(
                    EMGAcquisition(
                        acquisition_id="acq-" + acquisition_label,
                        base_path=self.root,
                        task=self,
                        _description=self._description,
                    )
                )

            # If no acquisitions are found, add a default one
            if not self._acquisitions:
                self._acquisitions.append(
                    EMGAcquisition(
                        acquisition_id="acq-00",
                        base_path=self.root,
                        task=self,
                        _description=self._description,
                    )
                )

        return self._acquisitions

    @acquisitions.setter
    def acquisitions(
        self, value: MutableSequence[str] | MutableSequence[EMGAcquisition]
    ) -> None:
        # numpydoc ignore=GL08
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, str) for entry in value):
                self._acquisitions = []
                for entry in value:
                    assert isinstance(entry, str)  # for mypy
                    self._acquisitions.append(
                        EMGAcquisition(
                            acquisition_id=entry,
                            base_path=self.root,
                            _description=self._description,
                        )
                    )
            elif all(isinstance(entry, EMGAcquisition) for entry in value):
                self._acquisitions = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError(
                "Field `Acquisitions` must be a list of EMGAcquisition objects"
            )

    def write(self, output_path: os.PathLike | str) -> None:  # noqa: ARG002 TODO: Remove
        """
        Write task-level EMG files.

        Parameters
        ----------
        output_path : os.PathLike | str
            The path where the output files will be written.

        Raises
        ------
        NotImplementedError
            If generic EMG task writing is requested while not-implemented
            behavior is enforced.
        """
        # TODO: implement writing of basic Task data
        if not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
            raise NotImplementedError


def parse_emg_json_sidecar(sidecar_path: pathlib.Path) -> dict:
    """
    Split an EMG JSON sidecar into task, hardware, institution, and EMG blocks.

    Parameters
    ----------
    sidecar_path : pathlib.Path
        Path to an EMG JSON sidecar file.

    Returns
    -------
    dict
        Grouped metadata blocks keyed by ``task``, ``hardware``,
        ``institution``, and ``emg``.
    """
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


def get_emg_channels(
    tsv_path: pathlib.Path | None,
    json_path: pathlib.Path | None,
) -> MutableSequence[EMGChannel]:
    """
    Build EMG channel objects from BIDS channel TSV/JSON files.

    Parameters
    ----------
    tsv_path : pathlib.Path | None
        Path to a BIDS ``*_channels.tsv`` file containing EMG channel definitions.
        If provided, channel data is parsed from the TSV file.
    json_path : pathlib.Path | None
        Path to a BIDS ``*_channels.json`` sidecar file containing channel metadata.
        If provided, column definitions are parsed from the JSON file.

    Returns
    -------
    MutableSequence[EMGChannel]
        List of :py:class:`EMGChannel` objects constructed from the parsed
        TSV and JSON metadata, with associated column information.

    See Also
    --------
    :py:class:`EMGChannel`
        Dataclass representing a single EMG channel definition.
    :py:func:`get_emg_electrodes`
        Similar function for building EMG electrode objects.

    Notes
    -----
    If both ``tsv_path`` and ``json_path`` are provided, column metadata from
    the JSON file is used to enrich the channel definitions from the TSV file.
    Either or both parameters can be ``None``, resulting in an empty list.
    """
    emg_channels: list[EMGChannel] = []
    columns = []

    if json_path:
        column_data = parse_json_sidecar(json_path)

        for column_name, column_values in column_data.items():
            columns.append(Column(name=column_name, **column_values))

    if tsv_path:
        data = parse_descriptive_tsv(tsv_path)
        for emg_channel in data:
            assert isinstance(emg_channel, dict), "Must be dicts in Generator."

            add_object_to_sequence(
                entity_list=emg_channels,
                entity_class=EMGChannel,
                columns=columns,
                **emg_channel,
            )

    return emg_channels


def get_emg_electrodes(
    tsv_path: pathlib.Path | None,
    json_path: pathlib.Path | None,
) -> MutableSequence[EMGElectrode]:
    """
    Build EMG electrode objects from BIDS electrode TSV/JSON files.

    Parameters
    ----------
    tsv_path : pathlib.Path | None
        Path to a BIDS ``*_electrodes.tsv`` file containing EMG electrode definitions.
        If provided, electrode data is parsed from the TSV file.
    json_path : pathlib.Path | None
        Path to a BIDS ``*_electrodes.json`` sidecar file containing electrode metadata.
        If provided, column definitions are parsed from the JSON file.

    Returns
    -------
    MutableSequence[EMGElectrode]
        List of :py:class:`EMGElectrode` objects constructed from the parsed
        TSV and JSON metadata, with associated column information.

    See Also
    --------
    :py:class:`EMGElectrode`
        Dataclass representing a single EMG electrode definition.
    :py:func:`get_emg_channels`
        Similar function for building EMG channel objects.

    Notes
    -----
    If both ``tsv_path`` and ``json_path`` are provided, column metadata from
    the JSON file is used to enrich the electrode definitions from the TSV file.
    Either or both parameters can be ``None``, resulting in an empty list.
    """
    emg_electrodes: list[EMGElectrode] = []
    columns = []

    if json_path:
        column_data = parse_json_sidecar(json_path)

        for column_name, column_values in column_data.items():
            columns.append(Column(name=column_name, **column_values))

    if tsv_path:
        data = parse_descriptive_tsv(tsv_path)
        for emg_electrode in data:
            assert isinstance(emg_electrode, dict), "Must be dicts in Generator."

            add_object_to_sequence(
                entity_list=emg_electrodes,
                entity_class=EMGElectrode,
                columns=columns,
                **emg_electrode,
            )

    return emg_electrodes


def _update_description_data(
    cls: EMGRecording | EMGRun | EMGAcquisition, file_name: str
):
    """
    Update inherited EMG metadata from nearby sidecars.

    Parameters
    ----------
    cls : EMGRecording or EMGRun or EMGAcquisition
        Object whose ``_description`` mapping should be updated.
    file_name : str
        Filename glob stem used to locate relevant sidecars.
    """
    _, json_path = get_tsv_json_files(cls.root, file_name + "emg")

    if json_path:
        if not cls._description:
            data = parse_emg_json_sidecar(json_path)
            data_clean = clean_dict(
                data,
                skip_keys_to_manipulate=ManipulateKeysOption.ALL_KEYS_MANIPULATE,
                string_manipulation=to_snakecase,
            )
            cls._description = data_clean
        else:
            data = parse_emg_json_sidecar(json_path)
            data_clean = clean_dict(
                data,
                skip_keys_to_manipulate=ManipulateKeysOption.ALL_KEYS_MANIPULATE,
                string_manipulation=to_snakecase,
            )
            cls._description.update(data_clean)
    else:
        warn(
            f"No EMG JSON sidecar file found for {cls._entity_name} {cls._entity_id} "
            f"in {cls.root}",
            FileNotFoundWarning,
        )

    tsv_path, json_path = get_tsv_json_files(cls.root, file_name + "electrodes")
    if tsv_path:
        electrodes = {"electrodes": get_emg_electrodes(tsv_path, json_path)}
        if not cls._description:
            cls._description = electrodes
        else:
            cls._description.update(electrodes)
    else:
        warn(
            f"No EMG electrodes TSV and JSON sidecar file found for {cls._entity_name} "
            f"{cls._entity_id} in {cls.root}",
            FileNotFoundWarning,
        )
