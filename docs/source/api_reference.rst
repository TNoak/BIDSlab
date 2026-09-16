API Reference
=============

This is the comprehensive API reference for the BIDSlab package. The following sections provide
detailed information about the various modules, classes, and functions available in BIDSlab.

Introduction
------------

BIDSlab provides a Python interface for working with BIDS (Brain Imaging Data Structure) datasets.
The package is organized into several main components:

- **Core modules** - Fundamental BIDS data structures and specifications
- **Extensions** - Support for BIDS extensions including e.g. Motion and EMG
- **IO operations** - Loading and saving BIDS datasets
- **Settings** - Package configuration and customization
- **Utilities** - Helper functions for data manipulation and validation, mainly intended for package internal use

Core API
~~~~~~~~

The core BIDS data structures represent the hierarchy of BIDS datasets:

.. toctree::
   :maxdepth: 2

   core

Extensions API
~~~~~~~~~~~~~~

Extended BIDS modalities for specialized data types:

.. toctree::
   :maxdepth: 2

   extensions

Core Functions
~~~~~~~~~~~~~~

Primary user-facing functions for IO and configuration:

.. toctree::
   :maxdepth: 1

   io
   settings

Utilities
~~~~~~~~~

Utility functions and classes supporting aBIDSkit operations:

.. toctree::
   :maxdepth: 2

   utils

Usage Patterns
--------------

**Loading a Dataset**

.. code-block:: python

   from bidslab import load_dataset

   dataset = load_dataset("/path/to/bids/dataset")
   print(f"Dataset: {dataset.name}")
   print(f"Subjects: {len(dataset.subjects)}")

**Accessing Data**

.. code-block:: python

   for participant in dataset.participants:
       for session in participant.sessions:
           for datatype in session.datatypes:
               print(f"{participant.participant_id}/{session.session_id}/{datatype.datatype_name}")

**Saving Modifications**

.. code-block:: python

   from abidskit import write_dataset

   write_dataset(dataset, "/path/to/output")

**Working with Extensions**

.. code-block:: python

   from abidskit.extensions.motion import MotionTask
   from abidskit.extensions.emg import EMGAcquisition

   # Motion capture data
   for participant in dataset.participants:
       for session in participant.sessions:
           for datatype in session.datatypes:
               if datatype.datatype_name == "motion":
                   # Process motion data
                   ...

   # EMG data
   for participant in dataset.participants:
       for session in participant.sessions:
           for datatype in session.datatypes:
               if datatype.datatype_name == "emg":
                   # Process EMG data
                   ...

Module Organization
-------------------

The BIDSlab package follows a hierarchical organization:

::

    bidlab/
    ├── core/                       # Core BIDS implementation
    │   ├── specs_dataset.py        # Dataset class
    │   ├── specs_datatype.py       # Datatype class
    │   ├── specs_task.py           # Task definitions
    │   ├── specs_misc.py           # Common entity classes
    │   ├── specs_phenotype.py      # Phenotypic data
    │   └── specs_summary.py        # Data summary classes
    ├── extensions/                 # BIDS extensions
    │   ├── motion.py               # Motion extension
    │   └── emg.py                  # Electromyography extension
    ├── io.py                       # Load and save datasets
    ├── settings.py                 # Configuration management
    └── utils/                      # Utility functions
        ├── helpers.py              # Data loading and transformation
        ├── checks.py               # Validation functions
        ├── exceptions.py           # Custom exceptions
        ├── string_manipulation.p   # String transformations
        └── dict_manipulation.py    # Dict transformations

Related Documentation
---------------------

- :doc:`../developer_guide` - Developer guidelines and conventions
