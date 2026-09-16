Internal API Reference
======================

This is the internal API reference for the BIDSlab package. It provides documentation for
internal classes, base classes, and type definitions used internally. Use this reference if
you want to write your own extensions or contribute to the development of BIDSlab.

Internal Modules
----------------

The following internal modules provide base classes and utilities for extending BIDSlab:

.. toctree::
   :maxdepth: 2

   common.base
   typing

Common Base Classes
~~~~~~~~~~~~~~~~~~~

The ``common.base`` module provides abstract base classes and mixins used throughout the
package. These classes form the foundation for implementing BIDS entity classes and
can be used when creating custom extensions.

Type Definitions
~~~~~~~~~~~~~~~~

The ``typing`` module provides generic types and protocol definitions used throughout the codebase.
These types ensure consistency and enable static type checking with mypy.

Extending BIDSlab
------------------

To create custom extensions or modify BIDSlab behavior:

1. **Study the base classes** - Understand the structure in ``common.base``
2. **Follow the patterns** - Look at existing extensions (motion, emg) as examples
3. **Use type hints** - Apply types from ``typing`` for consistency
4. **Follow conventions** - Adhere to numpy-style docstrings and code style guidelines
5. **Write tests** - Ensure your code works correctly with existing functionality

Creating a Custom Extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from bidslab.common.base import BaseTask

   class CustomTask(BaseTask):
       """Custom extended task for your modality.

       Parameters
       ----------
       task_length : int | None
           Length of the task.
       """

       def __init__(self, **kwargs: Any):
           """Initialize the entity."""
           self.task_length: int | None = kwargs.pop("task_length", None)
           super().__init__(**kwargs)
           # Implement initialization logic
           pass

For detailed guidelines on creating extensions, refer to the :doc:`../developer_guide`.

Related Documentation
---------------------

- :doc:`../api_reference` - Public API reference
- :doc:`../developer_guide` - Development guidelines and conventions
- :doc:`../extensions` - Existing BIDS extensions (motion, emg)
