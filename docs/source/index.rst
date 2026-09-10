####################################
Welcome to aBIDSkit's documentation!
####################################

aBIDSkit is a Python package for loading, manipulating, and saving BIDS (Brain Imaging Data Structure) datasets. This documentation provides comprehensive guides and API references for working with BIDS data programmatically.

.. note::

   aBIDSkit is currently in pre-alpha development. The API may change significantly in future releases.

.. warning::

   This documentation is only intended for the usage of aBIDSkit.
   For information on BIDS itself, please refer to the official BIDS documentation at https://bids.neuroimaging.io/ .
   https://bids-specification.readthedocs.io/en/stable is regarded as the single source of truth for the BIDS specification.
   Descriptions of BIDS entities and fields found in this API reference are merely intended as a convenience for users of aBIDSkit and may be outdated or incomplete.
   In case of discrepancies, the official BIDS documentation should always be considered authoritative.


Quick Start
===========

Load and explore a BIDS dataset:

.. code-block:: python

   from abidskit import load_dataset

   # Load a BIDS dataset
   dataset = load_dataset("/path/to/bids/dataset")

   # Access dataset information
   print(dataset.name)
   print(dataset.bids_version)

   # Save the dataset
   from abidskit import write_dataset
   write_dataset(dataset, "/path/to/output")


.. toctree::
   :hidden:

   .. getting_started
      user_guide

   api_reference

.. toctree::
   :hidden:
   :caption: Development

   .. changelog

   internal_api_reference
   developer_guide
   todo_list
