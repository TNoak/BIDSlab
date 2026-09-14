Exceptions Module
=================

The Exceptions module provides custom exception classes and warninigs for error handling
and reporting throughout the aBIDSkit package. These exceptions provide specific error
types for different failure conditions.

Overview
--------

Custom exceptions include:

- **BIDS validation errors** - Invalid dataset structure or entity violations
- **IO errors** - File reading/writing failures
- **Configuration errors** - Invalid settings or configuration
- **Value errors** - Invalid parameter values or constraints
- **File not found** - Missing required files or directories

Module API
----------

.. automodule:: abidskit.utils.exceptions
   :show-inheritance: True

Related Documentation
---------------------

- :doc:`utils.helpers` - Functions using these exceptions
- :doc:`utils.checks` - Validation functions that raise exceptions
- :doc:`../io` - IO operations with error handling
