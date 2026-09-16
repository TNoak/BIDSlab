Motion Capture Module
=====================

The Motion extension provides comprehensive support for motion capture and motion tracking data
within the BIDS specification. This includes data from optical, electromagnetic, inertial, and
other motion tracking systems.

Overview
--------

The extension includes support for:

- **Reference frames** - Define the spatial coordinate system and origin for motion data
- **Motion tracking systems** - Document the hardware and methods used for capturing motion
- **Task metadata** - Specify motion-specific task parameters and experimental conditions
- **Acquisition metadata** - Define motion recording settings and sampling rates

Module API
----------

.. automodule:: abidskit.extensions.motion
   :show-inheritance: True

Related Documentation
---------------------

- :doc:`extensions.emg` - Electromyography extension for synchronized muscle recordings
- :doc:`io` - Loading and saving datasets with motion modality
- :doc:`common.specs_misc` - Common entity definitions used by motion and other modalities
- :doc:`../developer_guide` - Guidelines for extending aBIDSkit with new modalities
