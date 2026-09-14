Electromyography (EMG) Module
=============================

The EMG extension provides comprehensive support for electromyography recordings within the BIDS
specification. This includes both surface EMG (sEMG) and intramuscular EMG recordings.

Overview
--------
The extension includes support for:

- **Coordinate systems** - Define the spatial relationship and positioning of EMG electrodes
- **Hardware specifications** - Document the recording equipment and electrode configuration
- **Task metadata** - Specify EMG-specific task parameters and experimental conditions
- **Acquisition metadata** - Define EMG-specific recording settings and parameters

Module API
----------

.. automodule:: abidskit.extensions.emg
   :show-inheritance: True

Related Documentation
---------------------

- :doc:`extensions.motion` - Motion capture extension for synchronized kinematic data
- :doc:`io` - Loading and saving datasets with EMG modality
- :doc:`common.specs_misc` - Common entity definitions used by EMG and other modalities
- :doc:`../developer_guide` - Guidelines for extending aBIDSkit with new modalities
