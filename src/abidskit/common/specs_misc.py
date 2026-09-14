"""
Miscellaneous BIDS entities and data structures.

This module provides various utility classes for representing BIDS metadata
entities such as hardware, institutions, data columns, and filtering
specifications.
"""

#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Iterable,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from warnings import warn

import pandas as pd

from abidskit._typing import A
from abidskit.common.base import BaseAcquisition, Entity
from abidskit.settings import get_settings_value
from abidskit.utils.checks import check_if_valid_uri
from abidskit.utils.exceptions import (
    FieldEntryNotValidError,
    TopLevelEntityNotLinkedWarning,
)
from abidskit.utils.helpers import (
    get_entity_from_file,
    get_tsv_json_files,
    load_tsv_data,
    set_attr_from_dict,
)
from abidskit.utils.string_manipulation import to_snakecase

if TYPE_CHECKING:
    from abidskit.common.specs_task import Task

# Allowed data format types for BIDS columns
FORMAT_ALLOWED_FIELD_ENTRIES = {
    "string",
    "number",
    "integer",
    "boolean",
    "index",
    "label",
    "date",
    "datetime",
    "time",
    "unit",
    "uri",
    "rrid",
    "bids_uri",
    "dataset_relative",
    "file_relative",
    "participant_relative",
    "stimuli_relative",
    "hed_version",
}


@dataclass(slots=True)
class Filter:
    """
    Represent a signal-processing filter specification.

    Attributes
    ----------
    name : str
        Human-readable filter name such as ``"bandpass"`` or ``"notch"``.
    parameters : MutableMapping[str, str]
        Mapping of parameter names to serialized values as they would appear in a
        BIDS JSON sidecar.

    See Also
    --------
    :py:class:`Hardware`
        Hardware metadata often documented alongside filter settings.

    Notes
    -----
    Filters are typically used to describe preprocessing or acquisition-chain
    operations applied to signal files in BIDS metadata.

    Examples
    --------
    >>> Filter(name="bandpass", parameters={"high_cutoff": "40", "low_cutoff": "1"})
    Filter(name='bandpass', parameters={'high_cutoff': '40', 'low_cutoff': '1'})
    """

    name: str
    parameters: MutableMapping[str, str]


@dataclass(slots=True)
class Level:
    """
    Represent a discrete categorical level for a BIDS TSV column.

    Attributes
    ----------
    level_name : str
        The name or value of the level.
    description : str
        A description of what this level represents.
    term_url : str, optional
        A URL to an ontology term defining this level.

    Raises
    ------
    ValueError
        If term_url is provided but is not a valid URI.

    See Also
    --------
    :py:class:`Column`
        Column metadata object that may aggregate multiple levels.

    Notes
    -----
    Levels are used in categorical columns to define the meaning of each
    distinct value. When ``term_url`` is provided, it is validated to ensure it
    conforms to URI standards expected by BIDS JSON sidecars.

    Examples
    --------
    >>> Level(level_name="left", description="Left-hand response")
    <Level name=left>
    """

    level_name: str
    description: str
    term_url: str | None = None

    def __post_init__(self) -> None:
        """
        Validate ontology metadata after initialization.

        Returns
        -------
        None
            The dataclass is validated in place.

        Raises
        ------
        ValueError
            Raised if :attr:`term_url` is present but is not a valid URI.

        Notes
        -----
        Validation is performed eagerly so invalid categorical metadata is caught
        before a :py:class:`Column` sidecar is written.
        """
        if self.term_url:
            check_if_valid_uri(self.term_url)

    def __repr__(self) -> str:
        """Return a string representation of the Level object."""
        return f"<Level name={self.level_name}>"


@dataclass(slots=True)
class Hardware:
    """
    Represent hardware or device metadata recorded in BIDS sidecars.

    Attributes
    ----------
    manufacturer : str, optional
        The name of the hardware manufacturer.
    manufacturers_model_name : str, optional
        The model name or number of the hardware.
    software_versions : str, optional
        The software version(s) running on the hardware.
    device_serial_number : str, optional
        The serial number of the device.

    See Also
    --------
    :py:class:`Institution`
        Institution-level metadata often reported together with hardware details.
    :py:class:`PhysioRecording`
        Recording class that can embed hardware information.

    Notes
    -----
    This class is used to document the specific hardware and software
    configuration used in data acquisition. It mirrors common manufacturer fields
    found across BIDS modality sidecars.

    Examples
    --------
    >>> Hardware(manufacturer="Elekta", manufacturers_model_name="VectorView")
    <Hardware manufacturer=Elekta model=VectorView>
    """

    manufacturer: str | None = None
    manufacturers_model_name: str | None = None
    software_versions: str | None = None
    device_serial_number: str | None = None

    def __repr__(self) -> str:
        """Return a string representation of the Hardware object."""
        return (
            f"<Hardware manufacturer={self.manufacturer} "
            f"model={self.manufacturers_model_name}>"
        )


@dataclass(slots=True)
class Institution:
    """
    Represent institution metadata associated with a BIDS acquisition site.

    Attributes
    ----------
    institution_name : str, optional
        The name of the institution.
    institution_address : str, optional
        The physical address of the institution.
    institutional_department_name : str, optional
        The name of the department within the institution.

    See Also
    --------
    :py:class:`Hardware`
        Acquisition-device metadata often stored alongside institution details.

    Notes
    -----
    This class is used to document the institution(s) responsible for
    data acquisition and processing. The fields correspond to common optional
    keys in BIDS sidecar metadata.

    Examples
    --------
    >>> Institution(institution_name="University Hospital")
    <Institution name=University Hospital>
    """

    institution_name: str | None = None
    institution_address: str | None = None
    institutional_department_name: str | None = None

    def __repr__(self) -> str:
        """Return a string representation of the Institution object."""
        return f"<Institution name={self.institution_name}>"


class Column:
    """
    Represents a data column specification in a BIDS TSV file.

    This class describes the properties of a column in a tabular (TSV) data
    file, including its name, format, units, and categorical levels.

    Parameters
    ----------
    name : str
        The name of the column as it appears in the TSV file.
    **kwargs : str | int | float | Mapping | Iterable
        Additional attributes to set on the column, such as long_name,
        description, format, units, etc.

    Attributes
    ----------
    column_name : str
        The name of the column.
    long_name : str, optional
        A longer, more descriptive name for the column.
    description : str, optional
        A description of what the column contains.
    format : str, optional
        The data format of the column values. Must be one of the values in
        :py:const:`FORMAT_ALLOWED_FIELD_ENTRIES`.
    units : str, optional
        The units of measurement for numeric columns.
    delimiter : str, optional
        The delimiter used to separate multiple values in a single cell.
    term_url : str, optional
        A URL to an ontology term defining this column.
    hed : str | Mapping[str, str], optional
        HED (Hierarchical Event Descriptors) tags for this column.
    maximum : int | float, optional
        The maximum value allowed in this column.
    minimum : int | float, optional
        The minimum value allowed in this column.

    Raises
    ------
    FieldEntryNotValidError
        If the format is not a valid BIDS format type.
    ValueError
        If term_url is provided but is not a valid URI.

    See Also
    --------
    :py:class:`Level`
        Categorical value definitions attached through :py:attr:`levels`.
    :py:class:`abidskit.common.specs_phenotype.PhenotypeColumn`
        Specialized phenotype-table column metadata.

    Notes
    -----
    The format property uses a custom setter to validate against allowed
    BIDS formats. Term URLs are validated when provided unless validation is
    explicitly overridden in settings. Levels support categorical-column
    documentation as described in BIDS JSON sidecars.

    Examples
    --------
    >>> Column(name="trial_type", format="string", levels={"go": "Go trial"})
    <Column name=trial_type format=string>
    """

    def __init__(
        self, name: str, **kwargs: str | int | float | Mapping | Iterable
    ) -> None:
        self.column_name: str = name

        self.long_name: str | None = None
        self.description: str | None = None
        self._format: str | None = None
        self.units: str | None = None
        self.delimiter: str | None = None
        self.term_url: str | None = None
        self.hed: str | Mapping[str, str] | None = None
        self.maximum: int | float | None = None
        self.minimum: int | float | None = None

        if get_settings_value("SUPPORT_OLD_VERSIONS"):
            self.unit: str | None = None

        self._levels: Iterable[Level] | None = None

        set_attr_from_dict(self, kwargs)

        if self.term_url and not get_settings_value("OVERRIDE_VALIDATION"):
            check_if_valid_uri(self.term_url)

    def __repr__(self) -> str:
        """Return a string representation of the Column object."""
        return f"<Column name={self.column_name} format={self.format}>"

    @property
    def format(self) -> str | None:
        # numpydoc ignore=RT01
        """Get the data format of the column values."""
        return self._format

    @format.setter  # noqa: A003
    def format(self, value: str) -> None:
        # numpydoc ignore=GL08
        if value not in FORMAT_ALLOWED_FIELD_ENTRIES:
            raise FieldEntryNotValidError(
                f"Field `Format` must be one of {FORMAT_ALLOWED_FIELD_ENTRIES}"
            )
        self._format = value

    @property
    def levels(self) -> Iterable[Level] | None:
        # numpydoc ignore=RT01
        """Get the categorical levels defined for this column."""
        return self._levels

    @levels.setter
    def levels(self, value: Mapping | Iterable[Level]) -> None:
        # numpydoc ignore=GL08
        if isinstance(value, Mapping):
            self._levels = []
            for key, val in value.items():
                if isinstance(val, Mapping):
                    val = {
                        to_snakecase(level_key): level_val
                        for level_key, level_val in val.items()
                    }
                    level = Level(level_name=key, **val)
                else:
                    level = Level(level_name=key, description=val)

                self._levels.append(level)
        elif isinstance(value, Iterable) and all(isinstance(v, Level) for v in value):
            self._levels = value
        else:
            raise TypeError("Field `Levels` must be a list of Level objects")


class Recording(Entity):
    """
    Represents a recording from a single physiological measurement device.

    This is a base class for different types of physiological recordings
    (e.g., cardiac, respiratory, electromyographic). It manages the data
    and metadata for a single recording session.

    Parameters
    ----------
    base_path : os.PathLike | str
        The file system path to the directory containing recording data.
    recording_id : str
        The unique identifier for this recording.
    sampling_frequency : int | float
        The sampling frequency of the recording in Hz.

    Attributes
    ----------
    recording_id : str
        The unique identifier for the recording.
    sampling_frequency : int | float
        The sampling frequency in Hz.
    root : pathlib.Path
        The file system path to the recording directory.

    See Also
    --------
    PhysioRecording : A subclass for physiological recordings with columns.
    Run : The Run entity that contains Recording objects.

    Notes
    -----
    Recordings are typically associated with a :py:class:`Run` entity and contain
    physiological data recorded during an experimental task or resting period.
    Sample tables are loaded lazily from BIDS physio TSV files when
    :py:attr:`data` is accessed.

    Examples
    --------
    >>> recording = Recording(base_path="ses-01", recording_id="resp", sampling_frequency=100)
    >>> recording.recording_id
    'resp'
    """

    def __init__(
        self,
        base_path: os.PathLike | str,
        recording_id: str,
        sampling_frequency: int | float,
    ):
        super().__init__(_entity_id=recording_id, _entity_name="recording")
        self.recording_id: str = self._entity_id
        self.sampling_frequency: int | float = sampling_frequency

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._data: Any = None

        self._run: Run | None = None

    @property
    def run(self) -> "Run | None":
        # numpydoc ignore=RT01
        """Get the parent Run object for this Recording."""
        if self._run:
            return self._run

        warn("Recording is not linked to a Run object.", TopLevelEntityNotLinkedWarning)
        return self._run

    @run.setter
    def run(self, value: "Run") -> None:
        # numpydoc ignore=GL08
        self._run = value

    @property
    def data(self):
        # numpydoc ignore=RT01
        """Get the recording data as a pandas DataFrame."""
        if self._data is None:
            # TODO: Rewrite to generalize for other data types than motion
            file_name = "*"
            # file_name = f"*{self.acquisition.tracking_system.tracking_system_id}*"
            # file_name += (
            #     f"_{self.acquisition.acquisition_id}"
            #     if len(self.acquisition.tracking_system.acquisitions) > 1
            #     else ""
            # )
            file_name += (
                f"_{self.run.run_id}" if len(self.run.acquisition.runs) > 1 else ""
            )
            file_name += f"_{self.recording_id}" if len(self.run.physio) > 1 else ""
            tsv_path, _ = get_tsv_json_files(
                self.run.root,
                file_name + "_physio",
            )
            data_frame = load_tsv_data(path=tsv_path, header=None)
            column_names = {}
            for column_number, column in enumerate(self.columns):
                column_names[column_number] = column.column_name
            data_frame.rename(columns=column_names, inplace=True)

            self._data = data_frame

        return self._data

    @data.setter
    def data(self, value: pd.DataFrame) -> None:
        # numpydoc ignore=GL08
        self._data = value

    def write(self, output_path: os.PathLike | str) -> None:
        """
        Write the recording to disk.

        Parameters
        ----------
        output_path : os.PathLike | str
            The file system path where the recording should be written.

        Returns
        -------
        Sequence[PhysioRecording]
            Physiological recordings associated with the run when implemented.

        Raises
        ------
        NotImplementedError
            If the recording write operation is attempted while
            ``IGNORE_NOT_IMPLEMENTED`` is disabled.

        Warnings
        --------
        This method is not yet implemented and will raise a NotImplementedError
        if the IGNORE_NOT_IMPLEMENTED setting is not enabled.
        """
        # TODO: implement writing of basic Recording data
        if not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
            raise NotImplementedError


class PhysioRecording(Recording):
    """
    Represents a physiological recording with defined columns.

    This class extends Recording to include column specifications and
    optional hardware information, typically used for data like cardiac
    rate, respiratory rate, or other physiological measurements.

    Parameters
    ----------
    base_path : os.PathLike | str
        The file system path to the directory containing recording data.
    recording_id : str
        The unique identifier for this recording.
    sampling_frequency : int
        The sampling frequency of the recording in Hz.
    start_time : int | float
        The start time of the recording relative to some reference point.
    columns : MutableSequence[Column]
        The column specifications for the data in this recording.
    hardware : Hardware, optional
        Information about the hardware used for this recording.

    Attributes
    ----------
    start_time : int | float
        The start time of the recording.
    columns : MutableSequence[Column]
        The column specifications.
    hardware : Hardware | None
        The hardware information.

    See Also
    --------
    Recording : The parent class for all recording types.
    Column : The column specification class.
    Hardware : Information about recording hardware.

    Notes
    -----
    PhysioRecording is typically used for recordings with well-defined column
    structures, as opposed to generic recording objects. It aligns with BIDS
    physiological recording sidecars that describe sampling frequency, start
    time, and channel columns.

    Examples
    --------
    >>> cols = [Column(name="cardiac", units="mV")]
    >>> PhysioRecording("ses-01", "cardiac", 1000, 0.0, cols)  # doctest: +SKIP
    """

    def __init__(
        self,
        base_path: os.PathLike | str,
        recording_id: str,
        sampling_frequency: int,
        start_time: int | float,
        columns: MutableSequence[Column],
        hardware: Hardware | None = None,
    ):
        super().__init__(
            base_path=base_path,
            recording_id=recording_id,
            sampling_frequency=sampling_frequency,
        )

        self.start_time: int | float = start_time
        self.columns: MutableSequence[Column] = columns
        self.hardware: Hardware | None = hardware


class Run(Entity, Generic[A]):
    """
    Represents a single experimental run or session.

    A Run is a continuous acquisition period within an acquisition context.
    It can contain physiological recordings, event markers, and other
    related data.

    Parameters
    ----------
    base_path : os.PathLike | str
        The file system path to the directory containing run data.
    run_id : int
        The numeric identifier for this run (must be an integer index).
    **kwargs : Any
        Additional attributes to set on the run.

    Attributes
    ----------
    run_id : str
        The run identifier as a string.
    root : pathlib.Path
        The file system path to the run directory.

    Raises
    ------
    TypeError
        If run_id is not an integer.

    See Also
    --------
    Acquisition : The parent acquisition entity that contains runs.
    Recording : Physiological recordings within a run.

    Notes
    -----
    Run IDs must be integers and are used to index multiple runs within
    a single acquisition context. The ID is stored internally as a string
    for compatibility with BIDS naming conventions.

    Examples
    --------
    >>> run = Run(base_path="ses-01", run_id=1)
    >>> run.run_id
    '1'
    """

    def __init__(self, base_path: os.PathLike | str, run_id: int, **kwargs: Any):
        if not isinstance(run_id, int):
            raise TypeError("run_id must be an index of type integer")
        run_id_str = str(run_id)
        super().__init__(_entity_id=run_id_str, _entity_name="run")
        self.run_id: str = self._entity_id

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._acquisition: A | None = None

        self._physio: Sequence[PhysioRecording] | None = None
        # self._events = None

        set_attr_from_dict(self, kwargs)

    def __repr__(self):
        """Return a string representation of the Run entity."""
        return f"Run id=run-{self.run_id}"

    @property
    def acquisition(self) -> A | None:
        # numpydoc ignore=RT01
        """Get the parent Acquisition object for this Run."""
        if self._acquisition:
            return self._acquisition

        warn(
            "Run is not linked to a Acquisition object.", TopLevelEntityNotLinkedWarning
        )
        return self._acquisition

    @acquisition.setter
    def acquisition(self, value: A) -> None:
        # numpydoc ignore=GL08
        self._acquisition = value

    @property
    def physio(self):
        """Get physiological recordings associated with this Run."""
        if not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
            raise NotImplementedError
        # if not self._physio:
        #     self._physio = []
        #     files = self.root.iterdir()
        #     physio_rec_ids = set()
        #     for file in files:
        #         try:
        #             physio_rec_ids.add(
        #                 get_entity_from_file(
        #                     file,
        #                     "recording",
        #                 )["recording"]
        #             )
        #         except KeyError:
        #             continue
        #     for rec_id in physio_rec_ids:
        #         _, json_path = get_tsv_json_files(
        #             self.root,
        #             f"*_{self.run_id}_{rec_id}_physio",
        #         )
        #         if json_path:
        #             data = parse_json_sidecar(json_path)
        #
        #             self._physio.append(
        #                 PhysioRecording(
        #                     recording_id=rec_id,
        #                     sampling_frequency=data.get("SamplingFrequency"),
        #                     start_time=data.get("StartTime"),
        #                     columns=data.get("Columns"),
        #                 )
        #             )
        #
        # return self._physio

    @physio.setter
    def physio(self, value: Sequence[dict] | Sequence[PhysioRecording]):
        # numpydoc ignore=GL08
        if not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
            raise NotImplementedError

    # @property
    # def events(self):
    #     raise NotImplementedError

    # @events.setter
    # def events(self, value: Sequence[dict] | Sequence[Event]):
    #     raise NotImplementedError

    def write(self, output_path: os.PathLike | str) -> None:
        """
        Write the run to disk.

        Parameters
        ----------
        output_path : os.PathLike | str
            The file system path where the run should be written.

        Warnings
        --------
        This method is not yet implemented and will raise a NotImplementedError
        if the IGNORE_NOT_IMPLEMENTED setting is not enabled.
        """
        # TODO: implement writing of basic Run data
        if not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
            raise NotImplementedError


class Acquisition(BaseAcquisition):
    """
    Represents an acquisition context within a datatype.

    An Acquisition groups multiple runs of the same acquisition, such as
    repeated measurements with the same equipment or parameters. Acquisitions
    are organized by datatype (e.g., MEG, EEG) and are associated with tasks.

    Parameters
    ----------
    base_path : os.PathLike | str
        The file system path to the acquisition directory.
    acquisition_id : str
        The unique identifier for the acquisition.

    Attributes
    ----------
    acquisition_id : str
        The unique identifier for the acquisition.
    root : pathlib.Path
        The file system path to the acquisition directory.
    runs : MutableSequence[Run]
        The runs associated with this acquisition.

    See Also
    --------
    Run : Individual run objects within an acquisition.
    Task : Task entities associated with acquisitions.

    Notes
    -----
    Acquisitions automatically discover and load runs from the file system.
    If no runs are found, a default run is created.

    Examples
    --------
    >>> acquisition = Acquisition(base_path="ses-01/meg", acquisition_id="acq-highres")
    >>> acquisition.runs  # doctest: +SKIP
    [Run id=run-0]
    """

    def __init__(self, base_path: os.PathLike | str, acquisition_id: str):
        super().__init__(base_path=base_path, acquisition_id=acquisition_id)

        self._task: Task | None = None

    @property
    def runs(self) -> MutableSequence[Run]:
        # numpydoc ignore=RT01
        """Get the runs associated with this Acquisition."""
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
                    Run(
                        run_id=run_id_int,
                        base_path=self.root,
                        acquisition=self,
                    )
                )

            # If no runs are found, add a default one
            if not self._runs:
                self._runs.append(
                    Run(
                        run_id=0,
                        base_path=self.root,
                        acquisition=self,
                    )
                )

        return self._runs

    @runs.setter
    def runs(self, value: Sequence[int | Run]) -> None:
        # numpydoc ignore=GL08
        if isinstance(value, Sequence):
            if all(isinstance(entry, int) for entry in value):
                self._runs = []
                for entry in value:
                    assert isinstance(entry, int)  # for mypy
                    self._runs.append(
                        Run(run_id=entry, base_path=self.root, acquisition=self)
                    )
            elif all(isinstance(v, Run) for v in value):
                self._runs = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Runs` must be a list of Run objects")

    @property
    def task(self) -> "Task | None":
        # numpydoc ignore=RT01
        """Get the task associated with this Acquisition."""
        if self._task:
            return self._task

        warn(
            "Acquisition is not linked to a Task object.",
            TopLevelEntityNotLinkedWarning,
        )
        return self._task

    @task.setter
    def task(self, value: "Task") -> None:
        # numpydoc ignore=GL08
        self._task = value
