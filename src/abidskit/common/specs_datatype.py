"""
Datatype entities in aBIDSkit.

This module provides the Datatype class for managing BIDS datatype entities,
which represent different types of data acquisitions (e.g., MEG, EEG, motion)
within a session. It handles loading, parsing, and organizing tasks associated
with each datatype.
"""

#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib
from typing import TYPE_CHECKING, Iterable, Mapping, Sequence
from warnings import warn

from abidskit.common.base import BaseTask
from abidskit.common.specs_task import Task
from abidskit.extensions.emg import EMGTask, parse_emg_json_sidecar
from abidskit.extensions.motion import MotionTask, parse_motion_json_sidecar
from abidskit.settings import get_settings_value
from abidskit.utils.dict_manipulation import ManipulateKeysOption, clean_dict
from abidskit.utils.exceptions import TopLevelEntityNotLinkedWarning
from abidskit.utils.helpers import (
    get_entity_from_file,
    get_tsv_json_files,
    set_attr_from_dict,
    write_entities,
)
from abidskit.utils.string_manipulation import to_snakecase

if TYPE_CHECKING:
    from abidskit.common.specs_summary import Session

# Datatypes that can contain task information in BIDS
DATATYPES_WITH_TASKS = {
    # "anat",  # needs special implementation
    "meg",
    "eeg",
    "ieeg",
    "beh",
    "pet",
    "nirs",
    "motion",
    "emg",
}


class Datatype:
    """
    Represents a datatype entity in a BIDS dataset.

    A Datatype represents a specific type of data acquisition (e.g., MEG, EEG,
    motion capture) within a session. It manages the tasks and runs associated
    with that datatype and provides methods to access and manipulate them.

    Parameters
    ----------
    base_path : os.PathLike | str
        The file system path to the datatype directory.
    datatype_name : str
        The name of the datatype (e.g., "meg", "eeg", "motion").
    **kwargs : Session | Iterable
        Additional keyword arguments to set as attributes, including a Session
        object if linking to a parent session.

    Attributes
    ----------
    datatype_name : str
        The name of the datatype.
    root : pathlib.Path
        The file system path to the datatype directory.

    Notes
    -----
    This class automatically discovers and loads tasks from the datatype
    directory based on the datatype name. Tasks are lazily loaded when accessed
    through the :py:attr:`tasks` property.

    See Also
    --------
    Session : The parent session entity that contains datatypes.
    Task : Individual task entities within a datatype.
    """

    def __init__(
        self,
        base_path: os.PathLike | str,
        datatype_name: str,
        **kwargs: "Session | Iterable",
    ) -> None:
        self.datatype_name: str = datatype_name

        self.root: pathlib.Path = pathlib.Path(base_path)

        self._session: Session | None = None

        self._tasks: Sequence[BaseTask] | None = None

        if kwargs:
            set_attr_from_dict(self, kwargs)

    def __repr__(self) -> str:
        """Return a string representation of the Datatype entity."""
        return f"<Datatype datatype_name={self.datatype_name}>"

    @property
    def session(self) -> "Session | None":
        """
        Get the parent Session object for this Datatype.

        Returns
        -------
        Session | None
            The parent :py:class:`~abidskit.common.specs_summary.Session` object,
            or None if not linked.

        Warns
        -----
        TopLevelEntityNotLinkedWarning
            If the Datatype is not linked to a Session object when accessed.
        """
        if self._session:
            return self._session

        warn(
            "Datatype is not linked to a Session object.",
            TopLevelEntityNotLinkedWarning,
        )
        return self._session

    @session.setter
    def session(self, value: "Session") -> None:
        """Set the parent Session object for this Datatype."""
        self._session = value

    @property
    def tasks(self) -> Sequence[BaseTask | Task | MotionTask]:
        """
        Get the tasks associated with this Datatype.

        Lazily loads and caches tasks from the datatype directory on first access.
        For datatypes with task support, parses task information from JSON sidecars.
        If no tasks are found, creates a default task.

        Returns
        -------
        Sequence[BaseTask | Task | MotionTask]
            A sequence of task objects associated with this datatype.

        Notes
        -----
        Tasks are lazily loaded on first access and cached. Supported datatypes for
        task loading are defined in :py:const:`DATATYPES_WITH_TASKS`. For datatypes
        with task support, the method automatically detects the task type (standard,
        motion, or EMG) and creates the appropriate task object.

        See Also
        --------
        Task : Standard task implementation.
        MotionTask : Motion capture task implementation.
        EMGTask : Electromyography task implementation.
        """
        if not self._tasks:
            self._tasks = []
            if self.datatype_name in DATATYPES_WITH_TASKS:
                files = self.root.iterdir()
                task_ids = set()
                for file in files:
                    try:
                        task_ids.add(
                            get_entity_from_file(
                                file,
                                "task",
                            )["task"]
                        )
                    except KeyError:
                        continue
                for task_id in task_ids:
                    _, json_path = get_tsv_json_files(
                        self.root, f"*task-{task_id}*_{self.datatype_name}"
                    )

                    if json_path:
                        if self.datatype_name == "motion":
                            data = parse_motion_json_sidecar(json_path)
                            task_name = data["task"].pop("TaskName")
                            self._tasks.append(
                                MotionTask(
                                    task_id="task-" + task_id,
                                    task_name=task_name,
                                    base_path=self.root,
                                    datatype=self,
                                    **data["task"],
                                )
                            )
                        elif self.datatype_name == "emg":
                            data = parse_emg_json_sidecar(json_path)
                            data_desc = clean_dict(
                                data,
                                skip_keys_to_manipulate=ManipulateKeysOption.ALL_KEYS_MANIPULATE,
                                string_manipulation=to_snakecase,
                            )
                            # TODO: add electrodes here
                            task_description = data_desc.pop("task", None)
                            task_name = task_description.pop("task_name", None)
                            description = {
                                "_description": data_desc,
                                **task_description,
                            }
                            self._tasks.append(
                                EMGTask(
                                    task_id="task-" + task_id,
                                    task_name=task_name,
                                    base_path=self.root,
                                    datatype=self,
                                    **description,
                                )
                            )
                        elif not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
                            raise NotImplementedError

                    elif not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
                        raise NotImplementedError

            elif not get_settings_value("IGNORE_NOT_IMPLEMENTED"):
                raise NotImplementedError

            # If no tasks are found, create a default one
            if not self._tasks:
                self._tasks.append(
                    Task(
                        task_name="n/a",
                        task_id="task-00",
                        base_path=self.root,
                        datatype=self,
                    )
                )

        return self._tasks

    @tasks.setter
    def tasks(self, value: Iterable[Mapping] | Iterable[BaseTask]) -> None:
        """
        Set the tasks associated with this Datatype.

        Parameters
        ----------
        value : Iterable[Mapping] | Iterable[BaseTask]
            Either a sequence of mappings (dictionaries) that will be converted to
            Task objects, or a sequence of BaseTask objects.

        Raises
        ------
        TypeError
            If the value is not an iterable of Mapping or BaseTask objects.

        Notes
        -----
        If mappings are provided, they will be converted to Task objects using the
        current :py:attr:`root` directory as the base path.
        """
        if isinstance(value, Iterable):
            if all(isinstance(entry, Mapping) for entry in value):
                self._tasks = []
                for entry in value:
                    assert isinstance(entry, Mapping)  # for mypy
                    self._tasks.append(Task(base_path=self.root, **entry))
            elif all(isinstance(entry, BaseTask) for entry in value):
                self._tasks = value  # type: ignore[assignment]  # mypy cannot type narrow on all()
        else:
            raise TypeError("Field `Tasks` must be a list of Task objects")

    def write(self, output_path: os.PathLike | str) -> None:
        """
        Write the datatype and its tasks to disk.

        Parameters
        ----------
        output_path : os.PathLike | str
            The file system path where the datatype directory should be written.

        See Also
        --------
        abidskit.utils.helpers.write_entities : Function for writing entities to disk.

        Notes
        -----
        This method writes all tasks associated with the datatype to the specified
        output path, creating the necessary directory structure.
        """
        write_entities(output_path, self.tasks)
