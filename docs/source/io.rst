IO Module
=========

The IO module provides functionality for loading and writing BIDS datasets. It is the primary
interface for users to interact with BIDS data stored on disk.

Overview
--------

The IO module handles:

- **Loading BIDS datasets** - Read and parse BIDS dataset structures from disk
- **Writing BIDS datasets** - Serialize dataset structures back to disk

Main Functions
--------------

**load_dataset(path, ...)**
  Load a complete BIDS dataset from disk. This function scans the dataset directory,
  reads all configuration files, and constructs a complete dataset structure.

**write_dataset(dataset, path, ...)**
  Save a dataset to disk. This function serializes the dataset structure and writes
  all modified files while maintaining BIDS compliance.

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from bidslab import load_dataset, write_dataset

   # Load a dataset
   dataset = load_dataset("/path/to/bids/dataset")

   # Access dataset information
   print(f"Dataset: {dataset.name}")
   print(f"BIDS Version: {dataset.bids_version}")
   print(f"Subjects: {len(dataset.subjects)}")

   # Modify the dataset
   for participant in dataset.participants:
       for session in participant.sessions:
           # Process data...
           pass

   # Save modifications
   write_dataset(dataset, "/path/to/output")

Working with Modalities
~~~~~~~~~~~~~~~~~~~~~~~~

Different data modalities can be accessed through the datatype hierarchy:

.. code-block:: python

   # Access motion data
   for participant in dataset.participants:
       for session in participant.sessions:
           for datatype in session.datatypes:
               if datatype.label == "motion":
                   # Work with motion data
                   pass

   # Access EMG data
   for participant in dataset.participants:
       for session in participant.sessions:
           for datatype in session.datatypes:
               if datatype.label == "emg":
                   # Work with EMG data
                   pass

Module API
----------

.. automodule:: abidskit.io
   :show-inheritance: True

BIDS Specification References
-----------------------------

For authoritative information about BIDS dataset structure and format, refer to:

- `BIDS Specification <https://bids-specification.readthedocs.io/en/stable/>`_
- Official BIDS documentation at https://bids.neuroimaging.io/
