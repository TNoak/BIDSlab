BIDS Core
=========

These subpackages provide the Python implementation for the specification of the BIDS core
standard. The core includes the fundamental data structures and concepts that apply across
all BIDS datasets.

Common Subpackage
-----------------

This subpackage contains the common specifications shared across all BIDS modalities and extensions.
It provides the foundational classes and entities upon which all other BIDS implementations are built.

Core Components
~~~~~~~~~~~~~~~

- **specs_dataset** - The root Dataset class representing an entire BIDS dataset
- **specs_datatype** - The Datatype class for modality-specific data (anat, func, motion, emg, etc.)
- **specs_task** - The Task class for experimental task definitions
- **specs_misc** - Common entity classes (Filter, Level, Hardware, etc.)
- **specs_phenotype** - Phenotypic and behavioral data structures
- **specs_summary** - Dataset-level summary files e.g. participants or sessions

Hierarchy
~~~~~~~~~

The BIDS hierarchy implemented by these modules:

::

    Dataset
    └── Participant
        └── Session
            ├── Datatype (anat, func, dwi, motion, emg, ...)
            │   └── Task
            │       └── Acquisition
            │           └── Run
            └── Phenotype

.. toctree::
   :maxdepth: 2

   common.specs_dataset
   common.specs_datatype
   common.specs_task
   common.specs_misc
   common.specs_phenotype
   common.specs_summary

Key Concepts
~~~~~~~~~~~~

**Dataset**
  The root container representing an entire BIDS-compliant dataset with all subjects,
  sessions, and modalities.

**Participant**
  Individual research participant or unit of observation (typically a person in
  neuroimaging studies).

**Session**
  Individual recording or assessment session for a subject (e.g., baseline, follow-up,
  intervention timepoint).

**Datatype**
  Modality-specific data container (e.g., structural anatomy, functional imaging,
  motion capture, electromyography).

**Task**
  Experimental task or condition with associated metadata.

**Acquisition**
  Specific recording configuration for a task.

**Run**
  Individual data file or measuring repetition with associated metadata.

BIDS Entities
~~~~~~~~~~~~~

The BIDS specification defines standard entities for organizing data:

- **sub** - Subject identifier
- **ses** - Session identifier
- **task** - Task identifier
- **acq** - Acquisition identifier
- **run** - Run index

Extended entities are defined by specific modalities and extensions.

Related Documentation
---------------------

- :doc:`extensions` - BIDS extensions including motion and EMG
- :doc:`io` - Loading and saving BIDS datasets
- :doc:`settings` - Package configuration
- :doc:`../developer_guide` - Guidelines for contributing new features
