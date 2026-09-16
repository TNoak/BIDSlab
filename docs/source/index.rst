####################################
Welcome to BIDSlab's documentation!
####################################

BIDSlab is a Python package for loading, manipulating, and saving BIDS (Brain Imaging Data Structure) datasets.
This documentation provides comprehensive guides and API references for working with BIDS data programmatically.

.. note::

   BIDSlab is currently in pre-alpha development. The API may change significantly in future releases.

.. warning::

   This documentation is only intended for the usage of BIDSlab.
   For information on BIDS itself, please refer to the official BIDS documentation at https://bids.neuroimaging.io/ .
   https://bids-specification.readthedocs.io/en/stable is regarded as the single source of truth for the BIDS specification.
   Descriptions of BIDS entities and fields found in this API reference are merely intended as a convenience for users of BIDSlab and may be outdated or incomplete.
   In case of discrepancies, the official BIDS documentation should always be considered authoritative.


Quick Start
===========

Install BIDSlab from PyPI:

.. code-block:: bash

   pip install bidslab

Load and explore a BIDS dataset:

.. code-block:: python

   from bidslab import load_dataset, write_dataset

   # Load a BIDS dataset
   dataset = load_dataset("/path/to/bids/dataset")

   # Access dataset information
   print(f"Dataset: {dataset.name}")
   print(f"BIDS Version: {dataset.bids_version}")
   print(f"Subjects: {len(dataset.subjects)}")

   # Explore dataset structure
   for subject in dataset.subjects:
       for session in subject.sessions:
           for datatype in session.datatypes:
               print(f"  {subject.label}/{session.label}/{datatype.label}")

   # Save modifications
   write_dataset(dataset, "/path/to/output")


Key Features
============

**🧠 Multi-Modality Support**
   Work with anatomical imaging, functional imaging, motion capture, and electromyography data
   in a unified, standardized format.

**📦 Complete BIDS Implementation (planned)**
   Full support for core BIDS specification with extensions.

**⚡ Efficient Data Access**
   Lazy-loading of data structures for memory-efficient handling of large datasets.

**🔍 Comprehensive Validation**
   Built-in validation ensures datasets conform to BIDS standards and specifications.

**🛠️ Developer-Friendly API**
   Clear, intuitive API with full type hints for seamless integration in Python workflows.

**📚 Well-Documented**
   Extensive API documentation with numpy-style docstrings and examples throughout.


Main Documentation Sections
=============================

.. toctree::
   :maxdepth: 2
   :caption: Using BIDSlab

   Quick Start Guide <#quick-start>
   .. user_guide

.. toctree::
   :maxdepth: 2
   :caption: Core Concepts

   api_reference

.. toctree::
   :maxdepth: 2
   :caption: Supported Modalities

   extensions

.. toctree::
   :maxdepth: 1
   :caption: Reference

   Common API <api_reference>
   Internal API <internal_api_reference>

.. toctree::
   :hidden:
   :caption: Development

   developer_guide
   internal_api_reference
   todo_list
   .. changelog


Supported BIDS Modalities
--------------------------

**Core Modalities (all planned)**
   - Anatomical imaging (anat)
   - Functional imaging (func)
   - Diffusion imaging (dwi)
   - Field maps (fmap)
   - Perfusion imaging (perf)

**Extensions**
   - :doc:`Motion Capture <extensions.motion>` - Optical, IMU, and video-based motion tracking
   - :doc:`Electromyography <extensions.emg>` - Surface and intramuscular EMG recordings

**Planned**
   - NIBS - Non-invasive brain stimulation
   - EEG - Electroencephalography
   - iEEG - Intracranial electroencephalography
   - MEG - Magnetoencephalography
   - MRS - Magnetic resonance spectroscopy
   - NIRS - Near-infrared spectroscopy
   - And more...


Getting Help
============

**API Documentation**
   Comprehensive reference documentation for all classes and functions is available in the
   :doc:`API Reference <api_reference>` section.

**Examples**
   Look for code examples in the docstrings of key functions like
   :py:func:`abidskit.load_dataset` and :py:func:`abidskit.write_dataset`.

**Development**
   For contributors and developers, see the :doc:`Developer Guide <developer_guide>` for
   guidelines on code style, testing, and documentation.

**Issues and Contributions**
   Report bugs and contribute improvements on GitHub at https://github.com/cimt-unia/abidskit


About BIDS
==========

The Brain Imaging Data Structure (BIDS) is a standard for organizing and describing
neuroimaging datasets. It provides a simple, standardized way to organize, describe,
and share neuroimaging and behavioral data.

Learn more about BIDS:

- **Official BIDS Specification**: https://bids-specification.readthedocs.io/
- **BIDS Community**: https://bids.neuroimaging.io/
- **BIDS Examples**: https://github.com/bids-standard/bids-examples


License
=======

aBIDSkit is licensed under the BSD-3-Clause License. See the LICENSE file in the repository for details.


Citation
========

If you use aBIDSkit in your research, please cite it appropriately. Citation information
will be available once the package is formally released.
