Misc Module
===========

The Misc module provides common entity classes and metadata containers shared across all BIDS
modalities. These classes represent fundamental concepts like levels, filters, hardware
specifications, and acquisition/recording metadata.

Overview
--------

The Misc module includes:

- **Entity classes** - Filter, Level, Hardware, Institution, Column definitions
- **Acquisition classes** - Recording, PhysioRecording configurations
- **Run management** - Run and Acquisition grouping for data files

Key Concepts
~~~~~~~~~~~~

**Filter**
  Metadata for hardware and software filters in timeseries-based modalities (e.g. EMG)

**Level**
  Description of levels for categorical data columns

**Hardware**
  Specification of recording equipment and sensors used in data acquisition

**Institution**
  Information about the institution where data was recorded

**Column**
  Definition of a data column with type and constraints (for tabular data)

**Recording**
  Continuous recordings of timeseries data

**PhysioRecording**
  Physiological recording including channels, sampling rates, and metadata

**Acquisition/Run**
  Individual acquisition and run instances and associated data

Module API
----------

.. automodule:: bidslab.common.specs_misc
   :show-inheritance: True

Related Documentation
---------------------

- :doc:`common.specs_dataset` - Dataset class using these entities
- :doc:`common.specs_datatype` - Datatype class using these entities
- :doc:`common.specs_task` - Task class using these entities
- :doc:`../extensions.motion` - Motion extension using misc classes
- :doc:`../extensions.emg` - EMG extension using misc classes
