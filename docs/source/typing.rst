Typing Subpackage
=================

The Typing subpackage provides type hints and type definitions used throughout aBIDSkit.
These types ensure consistency, enable static type checking, and improve IDE support.

Overview
--------

The Typing subpackage includes:

- **Base types** - Type definitions for core BIDS entities
- **Extension types** - Type definitions for extension-specific classes
- **Generic types** - Flexible type hints for polymorphic behavior
- **Type aliases** - Shorthand notation for complex types
- **Protocol definitions** - Structural subtyping for flexible APIs

Purpose
~~~~~~~

Type definitions enable:

- Static type checking with tools like mypy
- Better IDE autocompletion and error detection
- Clearer API documentation and contracts
- Flexible yet type-safe method signatures
- Easier debugging and code maintenance

Python Type Checking
~~~~~~~~~~~~~~~~~~~~

aBIDSkit uses Python's standard type hint system (PEP 484) to
provide comprehensive type information. All public APIs include type hints.

To check your code with mypy:

.. code-block:: bash

   mypy src/bidslab

Typing Modules
--------------

**Base Types** (`bidslab._typing.base`)
   Generic types for core BIDS entity classes including Acquisition, Run, and Task.

**Extension Types** (`bidslab._typing.extensions`)
   Type definitions for extension-specific classes including Motion and EMG entities.

Module API
----------

.. rubric:: Typing for base classes

.. automodule:: bidslab._typing.base
   :member-order: bysource

.. currentmodule:: bidslab._typing.base

.. rubric:: Typing for extension classes

.. automodule:: bidslab._typing.extensions
   :member-order: bysource

.. currentmodule:: bidslab._typing.extensions

Using Type Hints
----------------

Best practices for using type hints in aBIDSkit:

1. **Import types from typing module** - Use `from typing import ...`
2. **Use modern syntax** - Prefer `list[T]` over `List[T]` (Python 3.9+)
3. **Be specific** - Use Union/Optional only when necessary
4. **Document complex types** - Add Notes sections to docstrings when needed
5. **Test with mypy** - Run static type checking regularly

Example:

.. code-block:: python

   from typing import Optional, Sequence
   from bidslab.common.specs_dataset import Dataset

   def process_dataset(
       dataset: Dataset,
       subjects: Optional[Sequence[str]] = None,
   ) -> dict[str, any]:
       """Process a BIDS dataset.

       Parameters
       ----------
       dataset : Dataset
           The BIDS dataset to process.
       participants : Optional[Sequence[str]]
           List of participant ids to process. If None, all participants
           in the dataset are processed.

       Returns
       -------
       dict[str, any]
           Dictionary with processing results.
       """
       # Implementation...
       return {}

Related Documentation
---------------------

- :doc:`common.base` - Base classes using these types
- :doc:`internal_api_reference` - Complete internal API
- :doc:`../developer_guide` - Guidelines for type-safe development
