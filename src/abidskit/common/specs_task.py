"""Task-level BIDS specification classes.

This module provides the generic :py:class:`Task` implementation used to model
BIDS task entities and discover acquisition sub-entities from an existing
dataset tree.
"""

#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
from typing import TYPE_CHECKING, MutableSequence

from abidskit.common.base import BaseTask
from abidskit.common.specs_misc import Acquisition
from abidskit.settings import get_settings_value
from abidskit.utils.helpers import get_entity_from_file

if TYPE_CHECKING:
    from abidskit.common.specs_datatype import Datatype


class Task(BaseTask):
    """
    Represent a generic BIDS task entity.

    Parameters
    ----------
    base_path : os.PathLike or str
        Directory containing files for the task.
    task_name : str
        Human-readable task name used to derive the BIDS ``task-`` entity.
    **kwargs
        Additional task metadata and optional linked entities.

    Attributes
    ----------
    cog_atlas_id : str | None
        Optional Cognitive Atlas identifier for specialized task modalities.
    cog_poid : str | None
        Optional Cognitive Paradigm Ontology identifier.
    acquisitions : MutableSequence[Acquisition]
        Acquisition objects associated with this task.

    Notes
    -----
    The base implementation discovers acquisitions from filenames containing the
    ``acq-`` entity.

    See Also
    --------
    :py:class:`abidskit.common.base.BaseTask`
        Abstract base class providing common task behavior.
    :py:class:`abidskit.common.specs_misc.Acquisition`
        Acquisition entity loaded beneath a task.
    """

    def __init__(
        self,
        base_path: os.PathLike | str,
        task_name: str,
        **kwargs: "str | Datatype | MutableSequence",
    ) -> None:
        """
        Initialize a task entity.

        Parameters
        ----------
        base_path : os.PathLike or str
            Directory containing task-related files.
        task_name : str
            Name of the task used to derive ``task_id`` when omitted.
        **kwargs
            Additional task metadata applied to the instance.
        """
        self.cog_atlas_id = None  # !: Only for special datatypes
        self.cog_poid = None  # !: Only for special datatypes

        self._acquisitions: MutableSequence[Acquisition] | None = None

        super().__init__(base_path=base_path, task_name=task_name, **kwargs)

    @property
    def acquisitions(self) -> MutableSequence[Acquisition]:
        """
        Get acquisitions associated with the task.

        Returns
        -------
        MutableSequence[Acquisition]
            Acquisition objects discovered from task filenames.

        Notes
        -----
        The list is loaded lazily from the task directory. A default ``acq-00``
        acquisition is created when no explicit acquisition entity is found.

        See Also
        --------
        :py:class:`abidskit.common.specs_misc.Acquisition`
            Acquisition entity used by the generic task model.
        """
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
                    Acquisition(
                        acquisition_id="acq-" + acquisition_label,
                        base_path=self.root,
                    )
                )

            # If no acquisitions are found, add a default one
            if not self._acquisitions:
                self._acquisitions.append(
                    Acquisition(
                        acquisition_id="acq-00",
                        base_path=self.root,
                    )
                )

        return self._acquisitions

    @acquisitions.setter
    def acquisitions(self, value: MutableSequence[str | Acquisition]) -> None:
        """
        Set the acquisitions linked to this task.

        Parameters
        ----------
        value : MutableSequence[str | Acquisition]
            Acquisition identifiers or fully initialized
            :py:class:`abidskit.common.specs_misc.Acquisition` objects.

        Raises
        ------
        TypeError
            If ``value`` is not a mutable sequence of supported entries.
        """
        if isinstance(value, MutableSequence):
            if all(isinstance(entry, str) for entry in value):
                self._acquisitions = []
                for entry in value:
                    assert isinstance(entry, str)  # for mypy
                    self._acquisitions.append(
                        Acquisition(
                            acquisition_id=entry,
                            base_path=self.root,
                        )
                    )
            elif all(isinstance(v, Acquisition) for v in value):
                self._acquisitions = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError(
                "Field `Acquisitions` must be a list of Acquisition objects"
            )

    def write(self, output_path: os.PathLike | str) -> None:
        """
        Write task-level files to disk.

        Parameters
        ----------
        output_path : os.PathLike or str
            Destination directory for task content.

        Returns
        -------
        None
            This method is currently a placeholder.

        Warnings
        --------
        This method is not yet implemented and will raise a NotImplementedError
        if the IGNORE_NOT_IMPLEMENTED setting is not enabled.

        Notes
        -----
        Generic task serialization has not yet been implemented in aBIDSkit.
        """
        # TODO: implement writing of basic Task data
        if not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
            raise NotImplementedError
