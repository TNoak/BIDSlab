"""
Base classes for MRI extensions.

This module implements common classes used by the
specific MRI modalities.
"""

#  Copyright (c) 2026 by Lukas Behammer, Tobias Noak
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from bidslab.common.specs_misc import (
    Hardware,
    Institution,
)


@dataclass(slots=True)
class DeidentificationMethodCodeSequence:
    """
    Describes the mechanism used to protect the patients identity.

    Attributes
    ----------
    code_value : str | None, optional
        An identifier that is unambiguous within the Coding Scheme
        denoted by Coding Scheme Designator and Coding Scheme Version.
    code_meaning : str | None, optional
        Text that has meaning to a human and conveys the meaning of the term.
    coding_scheme_designator : str | None, optional
        The identifier of the coding scheme in which the coded entry is defined.
    coding_scheme_version : str | None, optional
        An identifier of the version of the coding scheme if
        necessary to resolve ambiguity.
    """

    code_value: str | None = None
    code_meaning: str | None = None
    coding_scheme_designator: str | None = None
    coding_scheme_version: str | None = None


@dataclass(slots=True)
class MRIHardware(Hardware):
    """
    Extend generic hardware metadata with MRI specific manufacturer fields.

    Attributes
    ----------
    station_name : str | None, optional
        Institution defined name of the machine that produced the measurements.
    hardcopy_device_software_version : str | None, optional
        Manufacturer's designation of the software of the device that created
        this Hardcopy Image (the printer).
    magnetic_field_strength : float | int | None, optional
        Nominal field strength of MR magnet in Tesla.
    recieve_coil_name : str | None, optional
        Information describing the receiver coil.
    recieve_coil_active_element : str | None, optional
        Information describing the active/selected elements of the receiver coil.
    number_recieve_coil_active_elements : int | None, optional
        The number of active RF elements used by the receive coil.
    gradient_set_type : str | None, optional
        It should be possible to infer the gradient coil from the scanner model, if not then
        the specifications of the actual gradient coil should be reported independently.
    mr_transmit_coil_sequence : str | None, optional
        This is a relevant field if a non-standard transmit coil is used.
    matrix_coil_mode : str | None, optional
        A method for reducing the number of independent channels by
        combining in analog the signals from multiple coil elements.
    coil_combination_method : str | None, optional
        The image reconstruction is changed by the coil combination
        method, so anything non-standard should be reported.
    number_transmit_coil_active_elements : int | None, optional
        The number of active RF elements used by the transmit coil.
    table_position : Sequence[int | float] | None, optional
        The table position, relative to an implementation-specific
        reference point, often the isocenter.
    """

    station_name: str | None = None
    hardcopy_device_software_version: str | None = None
    magnetic_field_strength: float | int | None = None
    recieve_coil_name: str | None = None
    recieve_coil_active_element: str | None = None
    number_recieve_coil_active_elements: int | None = None
    gradient_set_type: str | None = None
    mr_transmit_coil_sequence: str | None = None
    matrix_coil_mode: str | None = None
    coil_combination_method: str | None = None
    number_transmit_coil_active_elements: int | None = None
    table_position: Sequence[int | float] | None = None


@dataclass(slots=True)
class MRICommonMetadata:
    """
    Represent common MRI metadata fields.

    Attributes
    ----------
    hardware: MRIHardware | None, optional
        Hardware information.
    institution: Institution | None, optional
        Institution information.
    pulse_sequence_type : str | None, optional
        A general description of the pulse sequence used for the scan.
    scanning_sequence : Sequence[str] | str | None, optional
        Description of the type of data acquired.
    sequence_variant : Sequence[str] | str | None, optional
        Variant of the ScanningSequence.
    scan_options : Sequence[str] | str | None, optional
        Parameters of ScanningSequence.
    sequence_name : str | None, optional
        Manufacturer's designation of the sequence name.
    pulse_sequence_details : str | None, optional
        Information beyond pulse sequence type that
        identifies the specific pulse sequence used.
    nonlinear_gradient_correction : bool | None, optional
        Boolean stating if the image saved has been corrected
        for gradient nonlinearities by the scanner sequence.
    mr_acquisition_type : str | None, optional
        Type of sequence readout.
    mt_state : bool | None, optional
        Boolean stating whether the magnetization transfer pulse is applied.
    mt_offset_frequency : float | int | None, optional
        The frequency offset of the magnetization transfer pulse with
        respect to the central H1 Larmor frequency in Hertz (Hz).
    mt_pulse_bandwidth : float | int | None, optional
        The excitation bandwidth of the magnetization transfer pulse in Hertz (Hz).
    mt_number_of_pulses : float | int | None, optional
        The number of magnetization transfer RF pulses applied before the readout.
    mt_pulse_shape : str | None, optional
        Shape of the magnetization transfer RF pulse waveform.
    mt_pulse_duration : float | int | None, optional
        Duration of the magnetization transfer RF pulse in seconds.
    number_shots : Sequence[float | int] | float | int | None, optional
        The number of RF excitations needed to reconstruct a slice or volume.
    spoiling_state : bool | None, optional
        Boolean stating whether the pulse sequence uses any type of
        spoiling strategy to suppress residual transverse magnetization.
    spoiling_type : str | None, optional
        Specifies which spoiling method(s) are used by a spoiled sequence.
    spoiling_rf_phase_increment : float | int | None, optional
        The amount of incrementation described in degrees, which is applied to
        the phase of the excitation pulse at each TR period for achieving RF spoiling.
    spoiling_gradient_moment : float | int | None, optional
        Zeroth moment of the spoiler gradient lobe in
        millitesla times second per meter (mT.s/m).
    spoiling_gradient_duration : float | int | None, optional
        The duration of the spoiler gradient lobe in seconds.
    water_suppression : bool | None, optional
        Boolean indicating whether water suppression was used prior to acquisition.
    water_supression_technique : str | None, optional
        The name of the pulse sequence used for water suppression.
    b0_shimming_technique : str | None, optional
        The technique used to shim the B0 field.
    b1_shimming_technique : str | None, optional
        The technique used to shim the B1 field.
    parallel_reduction_factor_in_plane : float | int | None, optional
        The parallel imaging (for instance, SGRAPPA) factor in plane.
    parallel_reduction_factor_out_of_plane: float | int | None, optional
        The parallel imaging (for instance, GRAPPA) factor in the
        second phase encoding dimension of 3D sequences.
    parallel_acquisition_technique : str | None, optional
        The type of parallel imaging used (for example "GRAPPA", "SENSE").
    partial_fourier : float | int | None, optional
        The fraction of partial Fourier information collected.
    partial_fourier_direction : str | None, optional
        The direction where only partial Fourier information was collected.
    effective_echo_spacing : float | int | None, optional
        The ”effective” sampling interval, specified in seconds, between
        lines in the phase-encoding direction, defined based on the size
        of the reconstructed image in the phase direction.
    mixing_time : float | int | None, optional
        In the context of a stimulated- and spin-echo 3D EPI sequence for B1+ mapping or a
        stimulated-echo MRS sequence, corresponds to the interval between spin- and
        stimulated-echo pulses. In the context of a diffusion-weighted double spin-echo
        sequence, corresponds to the interval between two successive diffusion
        sensitizing gradients, specified in seconds.
    phase_encoding_direction : str | None, optional
        The letters i, j, k correspond to the first, second and third axis of the data in
        the NIFTI file. The polarity of the phase encoding is assumed to go from zero
        index to maximum index unless - sign is present (then the order is
        reversed - starting from the highest index instead of zero).
    total_readout_time : float | int | None, optional
        This is actually the ”effective” total readout time, defined as the readout
        duration, specified in seconds, that would have generated data with the
        given level of distortion.
    echo_time : Sequence[float | int] | float | int | None, optional
        The echo time (TE) for the acquisition, specified in seconds.
    inversion_time : float | int | None, optional
        The inversion time (TI) for the acquisition, specified in seconds.
    dwell_time : float | int | None, optional
        Actual dwell time (in seconds) of the receiver per point
        in the readout direction, including any oversampling.
    acquisition_duration : float | int | None, optional
        Duration (in seconds) of scan acquisition,
        including all volumes for multi-volume scans.
    slice_timing : Sequence[float | int] | None, optional
        The time at which each slice was acquired
        within each volume (frame) of the acquisition.
    slice_encoding_direction : str | None, optional
        The axis of the NIfTI data along which slices were acquired,
        and the direction in which "SliceTiming" is defined.
    flip_angle : Sequence[float | int] | float | int | None, optional
        Flip angle (FA) for the acquisition, specified in degrees.
    negative_contrast : bool | None, optional
        Value specifying whether increasing voxel intensity (within sample voxels)
        denotes a decreased value with respect to the contrast suffix.
    multiband_acceleration_factor : float | int | None, optional
        The multiband factor, for multiband acquisitions.
    anatomical_landmark_coordinates : Mapping[str, Sequence[float]] | None, optional
        Key-value pairs of the labels and 3-D digitized
        position of anatomical landmarks.
    b0_field_identifier : Sequence[str] | str | None, optional
        Unique string within one participant's tree, shared only by the images meant to be
        used as inputs for the estimation of a particular instance of the B0 field estimation.
    b0_field_source : Sequence[str] | str | None, optional
        This field states the B0 field estimation designated by the "B0FieldIdentifier" that
        may be used to correct the dataset for distortions caused by B0 inhomogeneities.
    body_part : str | None, optional
        Body part of the organ / body region scanned.
    body_part_details : str | None, optional
        Additional details about body part or location.
    body_part_details_ontology : str | None, optional
        BodyPartDetailsOntology of ontology used for BodyPartDetails.
    deidentification_method : Sequence[str] | None, optional
        A description of the mechanism or method used to remove the Patient's identity.
    deidentification_method_code_sequence : Sequence[DeidentificationMethodCodeSequence] | None, optional
        A sequence of code objects describing the mechanism or
        method use to remove the Patient's identity.
    """

    # Hardware
    hardware: MRIHardware | None = None

    # Institution
    institution: Institution | None = None

    # Sequence Specifics
    pulse_sequence_type: str | None = None
    scanning_sequence: Sequence[str] | str | None = None
    sequence_variant: Sequence[str] | str | None = None
    scan_options: Sequence[str] | str | None = None
    sequence_name: str | None = None
    pulse_sequence_details: str | None = None
    nonlinear_gradient_correction: bool | None = None
    mr_acquisition_type: str | None = None
    mt_state: bool | None = None
    mt_offset_frequency: float | int | None = None
    mt_pulse_bandwidth: float | int | None = None
    mt_number_of_pulses: float | int | None = None
    mt_pulse_shape: str | None = None
    mt_pulse_duration: float | int | None = None
    number_shots: Sequence[float | int] | float | int | None = None
    spoiling_state: bool | None = None
    spoiling_type: str | None = None
    spoiling_rf_phase_increment: float | int | None = None
    spoiling_gradient_moment: float | int | None = None
    spoiling_gradient_duration: float | int | None = None
    water_suppression: bool | None = None
    water_supression_technique: str | None = None
    b0_shimming_technique: str | None = None
    b1_shimming_technique: str | None = None

    # In- and Out-of-Plane Spatial Encoding
    parallel_reduction_factor_in_plane: float | int | None = None
    parallel_reduction_factor_out_of_plane: float | int | None = None
    parallel_acquisition_technique: str | None = None
    partial_fourier: float | int | None = None
    partial_fourier_direction: str | None = None
    effective_echo_spacing: float | int | None = None
    mixing_time: float | int | None = None
    phase_encoding_direction: str | None = None
    total_readout_time: float | int | None = None

    # Timing Parameters
    echo_time: Sequence[float | int] | float | int | None = None
    inversion_time: float | int | None = None
    dwell_time: float | int | None = None
    acquisition_duration: float | int | None = None
    slice_timing: Sequence[float | int] | None = None
    slice_encoding_direction: str | None = None

    # RF and Contrast
    flip_angle: Sequence[float | int] | float | int | None = None
    negative_contrast: bool | None = None

    # Slice Acceleration
    multiband_acceleration_factor: float | int | None = None

    # Anatomical landmarks
    anatomical_landmark_coordinates: Mapping[str, Sequence[float]] | None = None

    # Echo-Planar Imaging and B0 mapping
    b0_field_identifier: Sequence[str] | str | None = None
    b0_field_source: Sequence[str] | str | None = None

    # Tissue description
    body_part: str | None = None
    body_part_details: str | None = None
    body_part_details_ontology: str | None = None

    # Deidentification information
    deidentification_method: Sequence[str] | None = None
    deidentification_method_code_sequence: (
        Sequence[DeidentificationMethodCodeSequence] | None
    ) = None
