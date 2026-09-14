Datatype Module
===============

The Datatype module provides the representation for modality-specific data structures in BIDS.
A Datatype contains all data and metadata for a specific neuroimaging modality (e.g., anatomical,
functional, motion, EMG) within a session.

Overview
--------

The Datatype class represents:

- **Modality information** - The type of data (anat, func, dwi, motion, emg, etc.)
- **Task collection** - All tasks associated with this datatype
- **Session context** - Link to parent session and subject
- **Modality-specific metadata** - Datatype-specific configuration and settings
- **Lazy-loading** - Efficient data access without loading all files into memory

Modalities
~~~~~~~~~~

Supported modalities include:

.. Comment
- **anat** - Anatomical images (T1w, T2w, FLAIR, etc.)
- **func** - Functional images (fMRI, BOLD, etc.)
- **dwi** - Diffusion-weighted images
- **fmap** - Field maps
- **perf** - Perfusion images

- **motion** - Motion capture and tracking data
- **emg** - Electromyography recordings

.. Comment
- **eeg** - Electroencephalography (planned)
- **meg** - Magnetoencephalography (planned)

Module API
----------

.. automodule:: abidskit.common.specs_datatype
   :show-inheritance: True

Related Documentation
---------------------

- :doc:`common.specs_dataset` - Dataset class containing datatypes
- :doc:`common.specs_task` - Task definitions
- :doc:`common.specs_misc` - Entity definitions and metadata
- :doc:`../extensions.motion` - Motion capture extension
- :doc:`../extensions.emg` - Electromyography extension
