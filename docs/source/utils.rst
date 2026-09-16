Utils Subpackage
================

This subpackage provides utility functions and classes that support various operations
within the BIDSlab package. These utilities handle data transformation, validation,
error handling, and various helper functions used across the codebase.

Overview
--------

The utils subpackage includes:

- **helpers** - Utility functions for data loading, parsing, and transformation
- **checks** - Validation and constraint checking functions
- **exceptions** - Custom exception classes for error handling
- **string_manipulation** - String processing and formatting utilities
- **dict_manipulation** - Dictionary and mapping utilities

Key Utilities
~~~~~~~~~~~~~

**Data Loading**
  Functions for loading various data formats (EDF, TSV, JSON) and parsing BIDS sidecars

**Validation**
  Constraint checking and type validation for BIDS entities and data structures

**Exception Handling**
  Custom exceptions for specific error conditions and user-friendly error messages

**String Processing**
  Utilities for BIDS entity parsing, filename generation, and text manipulation

**Dictionary Operations**
  Utilities for nested dictionary manipulation and attribute setting

Module Organization
~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   utils.exceptions
   utils.helpers
   utils.checks
   utils.string_manipulation
   utils.dict_manipulation

Related Documentation
---------------------

- :doc:`io` - High-level IO operations using these utilities
- :doc:`settings` - Package configuration and settings
- :doc:`../developer_guide` - Development guidelines for utility development
