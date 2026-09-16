Task Module
===========

The Task module provides the representation for experimental task definitions in BIDS datasets.
Tasks define structured activities that subjects perform during data acquisition, along with
associated metadata and acquisition-specific configurations.

Overview
--------

The Task class represents:

- **Task identification** - Task name and unique identifier
- **Task description** - Documentation of what the task involves
- **Acquisition collection** - Multiple acquisition configurations for the task
- **Task metadata** - Stimulus timing, trial structure, and behavioral parameters
- **Datatype context** - Link to parent datatype and modality

Task Types
~~~~~~~~~~

Tasks can be:

- **Experimental tasks** - Structured behavioral tasks (e.g., n-back, Stroop, motor tasks)
- **Clinical assessments** - Standardized clinical evaluation protocols
- **Naturalistic tasks** - Recording during natural activities (watching movies, rest, etc.)
- **Resting state** - No specific task (rest, baseline conditions)
- **Custom tasks** - User-defined task protocols

Key Features
~~~~~~~~~~~~

- Complete task specification with behavioral parameters
- Event timing and stimulus information
- Multiple acquisition configurations per task
- Full metadata documentation

Module API
----------

.. automodule:: bidslab.common.specs_task
   :show-inheritance: True

Related Documentation
---------------------

- :doc:`common.specs_datatype` - Datatype containing tasks
- :doc:`common.specs_misc` - Acquisition and run definitions
- :doc:`../extensions.motion` - Motion-specific task types
- :doc:`../extensions.emg` - EMG-specific task types
