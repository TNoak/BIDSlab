Dataset Module
==============

The Dataset module provides the central data structure for representing BIDS datasets.
The Dataset class is the root object that contains all subject data and metadata for a
BIDS-compliant neuroimaging dataset.

Overview
--------

The Dataset class represents:

- **Dataset metadata** - Information about the dataset itself (name, BIDS version, etc.)
- **Subject collection** - All subjects in the dataset
- **Phenotypic data** - Behavioral and clinical phenotype information

Key Features
~~~~~~~~~~~~

- Complete BIDS compliance checking
- Hierarchical subject/session/datatype/task/acquisition structure
- Lazy-loading of data files for memory efficiency
- Support for all BIDS modalities and extensions (Currently only for some modalities)
- Comprehensive metadata management

Structure
~~~~~~~~~

A Dataset contains:

- **Participants** - Individual participants or research subjects
    - **Sessions** - Individual recording or assessment sessions per subject
        - **Datatypes** - Modality-specific data (anat, func, motion, emg, etc.)
            - **Tasks** - Information about the performed task
                - **Acquisitions** - Specific acquisition configurations
                    - **Runs** - Individual repetitions of measurements

Following the BIDS standard, some of those are optional.

Module API
----------

.. automodule:: abidskit.common.specs_dataset
   :show-inheritance: True

Related Documentation
---------------------

- :doc:`common.specs_datatype` - Datatype class for modality-specific data
- :doc:`common.specs_task` - Task definition for experimental tasks
- :doc:`common.specs_misc` - Entity classes and metadata containers
- :doc:`../io` - Loading and saving datasets
