Extensions subpackage
---------------------

This subpackage provides Python implementations for BIDS extensions. Extensions add support for
additional data modalities and specialized data types beyond the core BIDS specification.

Currently Implemented
=====================

The following extensions are fully implemented and documented:

**Motion** - Support for motion capture and tracking data including reference frames,
coordinate systems, and motion-specific task and acquisition metadata.

**Electromyography (EMG)** - Support for surface and intramuscular electromyography recordings
including electrode placement, coordinate systems, and EMG-specific task and acquisition metadata.

.. toctree::
   :maxdepth: 2

   extensions.motion
   extensions.emg
