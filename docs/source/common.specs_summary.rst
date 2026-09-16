Summary Module
==============

The Summary module provides data structures for common metadata before the
modality / datatype hierarchical level.
These include information about the dataset's individual data files, participants, and sessions.

Overview
--------

The Summary module handles information from "data summary files" such as, for example, ``participant.tsv`` files.
It implements classes to store metadata for participants, sessions and scans.

Module API
----------

.. automodule:: bidslab.common.specs_summary
   :show-inheritance: True

Related Documentation
---------------------

- :doc:`common.specs_dataset` - Dataset class generating summaries
- :doc:`common.specs_datatype` - Datatype information included in summaries
- :doc:`../io` - Loading datasets and accessing summary information
