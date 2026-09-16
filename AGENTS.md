# BIDSlab Documentation Standards for Agents

This document establishes the comprehensive documentation style and quality standards for the BIDSlab package. All agents and contributors should follow these conventions to maintain consistency, professionalism, and clarity across the entire codebase and documentation.

## Overview

BIDSlab uses **numpy-style docstrings** (PEP 257 compatible) with **Sphinx/Napoleon** for automated documentation generation. The documentation is dual-layered: RST files provide architectural context and examples, while Python docstrings provide detailed API reference documentation.

## Numpy-Style Docstring Format

All Python docstrings must follow numpy conventions with these sections in order:

### Section Structure

1. **Summary** (Required)

   - Single-line, imperative mood, present tense
   - Example: "Load a BIDS dataset from disk."
   - NOT: "Loads a BIDS dataset" or "Loading a BIDS dataset"

1. **Extended Summary** (Optional for simple functions, required for complex classes)

   - One or more paragraphs explaining the purpose, behavior, and context
   - Include relevant background information and use cases
   - Link to related concepts with proper cross-references

1. **Parameters** (Required if function/class takes arguments)

   - Format: `name : type` followed by description
   - Multi-type parameters: `type1 | type2`
   - Optional parameters: specify with "optional"
   - Example:
     ```
     Parameters
     ----------
     path : str or os.PathLike
         The file system path to load data from.
     recursive : bool, optional
         Whether to recursively load subdirectories. Default is False.
     ```

1. **Returns** (Required for functions that return values)

   - Format: `type` followed by description
   - For multiple return values, list each
   - Example:
     ```
     Returns
     -------
     dict
         A dictionary containing the loaded dataset with keys for each entity.
     ```

1. **Raises** (Recommended for error-prone functions/classes)

   - List all exceptions the code can raise
   - Include condition that triggers each exception
   - Only one "Raises" section per docstring (never duplicate)
   - Example:
     ```
     Raises
     ------
     FileNotFoundError
         If the specified path does not exist.
     ValueError
         If the dataset structure is invalid.
     ```

1. **Warnings** (Use when applicable)

   - For deprecations, experimental features, or important caveats
   - Example:
     ```
     Warnings
     --------
     This functionality is experimental and may change in future releases.
     ```

1. **See Also** (Recommended for classes and important functions)

   - Related functions/classes using proper cross-references
   - Use :py:class:, :py:func:, :py:meth: with tilde (~) for short display
   - Example:
     ```
     See Also
     --------
     :py:func:`~bidslab.io.write_dataset`
         Write a dataset to disk.
     :py:class:`~bidslab.common.Dataset`
         Core dataset class.
     ```

1. **Notes** (Recommended for non-trivial code)

   - Implementation details, algorithm explanations
   - BIDS-specific conventions and rationale
   - Performance considerations
   - Example:
     ```
     Notes
     -----
     This function automatically discovers entities according to BIDS
     hierarchical structure. Lazy loading is used to minimize memory overhead
     for large datasets.
     ```

1. **Examples** (Highly recommended for all public classes/functions)

   - Practical, executable code snippets
   - Use `# doctest: +SKIP` for examples requiring external data/setup
   - Demonstrate common use cases and workflows
   - Example:
     ```
     Examples
     --------
     >>> from bidslab import load_dataset
     >>> dataset = load_dataset("path/to/dataset")  # doctest: +SKIP
     >>> dataset.subjects
     ['sub-01', 'sub-02']
     ```

## Cross-Reference Conventions

Use proper Sphinx cross-reference syntax:

- **Classes**: `:py:class:`~module.ClassName\`\`
- **Functions**: `:py:func:`~module.function_name\`\`
- **Methods**: `:py:meth:`~module.ClassName.method_name\`\`
- **Modules**: `:py:mod:`~module.name\`\`

The tilde (~) shortens display to only the last component (e.g., "ClassName" instead of "module.ClassName").

## Quality Standards

### Code Coverage Requirements

- **All public classes** must have comprehensive docstrings
- **All public functions/methods** must have comprehensive docstrings
- **All parameters and returns** must be documented
- **Complex logic** must have explanatory docstrings
- **Exceptions** must be documented for error-prone code

### Documentation Quality Metrics

1. **Docstring Length**

   - Simple functions: 100+ characters
   - Complex classes: 500+ characters
   - Core classes: 1000+ characters

1. **Section Completeness**

   - Simple functions: Summary, Parameters, Returns, Raises
   - Complex classes: All 9 sections with emphasis on Notes and Examples
   - Extension classes: Comprehensive with extended summary and multiple examples

1. **Example Quality**

   - Every public class should have at least one example
   - Every user-facing function should have at least one example
   - Examples should demonstrate typical usage patterns
   - Examples requiring external data should use `# doctest: +SKIP`

1. **Special Considerations**

   - Only the getter methods of properties are documented with a one-line description with the docstring prepanded by `# numpydoc ignore=RT01` on the line above the docstring
   - The setter method is not documented and has a `# numpydoc ignore=GL08` in place of a docstring

## RST Documentation Structure

RST files provide context and examples at the module level:

### File Organization

```
docs/source/
├── index.rst                    # Homepage with features and use cases
├── core.rst                     # BIDS hierarchy and core concepts
├── extensions.rst               # Extension overview
├── extensions.motion.rst        # Motion capture documentation
├── extensions.emg.rst           # EMG modality documentation
├── io.rst                       # I/O functions and patterns
├── api_reference.rst            # Main API reference
├── common.*.rst                 # Core module pages
└── utils.*.rst                  # Utility module pages
```

### RST Section Pattern

Each module RST file should contain:

1. **Module Overview** - Purpose and scope of the module
1. **Architecture** - How components fit together
1. **Key Concepts** - Important terminology and patterns
1. **Usage Examples** - Common workflows with code
1. **API Reference** - Automodule directive pulling Python docstrings
1. **See Also** - Links to related modules if applicable

## Ruff Documentation Checks

The project uses Ruff with `select=["D"]` for documentation linting:

- **D100**: Module docstring required
- **D101**: Class docstring required
- **D102**: Public method docstring required
- **D103**: Function docstring required
- **D204**: Blank line required after class docstring before fields
- **D401**: Docstring must be in imperative mood

All checks must pass cleanly (0 issues).

## Sphinx Build Requirements

Documentation must build successfully with Sphinx:

- **Extensions used**: autodoc, napoleon, numpydoc
- **Theme**: pydata-sphinx-theme
- **Build command**: `python -m sphinx -b html docs/source docs/build/html`

## Consistency and Voice

### Terminology

- Use consistent terminology throughout the package
- BIDS-specific terms: entity, datatype, modality, run, session, task
- Technical terms: sampling frequency, coordinate system, reference frame

### Writing Style

- **Imperative mood**: "Load the dataset", not "Loads the dataset"
- **Present tense**: "This function loads", not "This function will load"
- **Active voice**: "The function returns a dict", not "A dict is returned"
- **Concise**: Avoid redundancy and unnecessary words
- **Professional**: Maintain a consistent, professional tone

### Documentation Tone

- Clear and direct for users
- Informative for developers
- Technically accurate for domain experts
- Accessible to newcomers learning BIDS/modalities

## Common Patterns

### For Classes

```python
class MotionAcquisition(BaseAcquisition):
    """
    Represents a motion capture acquisition within a session.

    [Extended summary explaining the acquisition, its role in the hierarchy,
     and when/how to use it. Include BIDS context and typical workflows.]

    Parameters
    ----------
    base_path : os.PathLike | str
        The file system path to the acquisition directory.
    acquisition_id : str
        The unique identifier for the acquisition (e.g., "acq-highres").

    Attributes
    ----------
    acquisition_id : str
        The unique identifier for the acquisition.
    runs : MutableSequence[MotionRun]
        The motion capture runs within this acquisition.

    See Also
    --------
    :py:class:`~bidslab.extensions.motion.MotionRun`
        Individual motion capture run.
    :py:class:`~bidslab.extensions.motion.MotionTask`
        Task metadata for motion acquisitions.

    Notes
    -----
    Motion acquisitions automatically discover runs from the file system
    following BIDS directory structure conventions.

    Examples
    --------
    >>> acq = MotionAcquisition(
    ...     base_path="ses-01/motion",
    ...     acquisition_id="acq-highres"
    ... )
    >>> len(acq.runs)  # doctest: +SKIP
    3
    """
```

### For Functions

```python
def load_dataset(path: str | os.PathLike) -> Dataset:
    """
    Load a BIDS dataset from disk.

    [Extended summary explaining the loading process, validation, and
     what the returned dataset contains.]

    Parameters
    ----------
    path : str or os.PathLike
        The file system path to the dataset directory.

    Returns
    -------
    Dataset
        A loaded dataset object with lazy-loaded entities.

    Raises
    ------
    FileNotFoundError
        If the path does not exist.
    ValueError
        If the dataset structure is invalid.

    See Also
    --------
    :py:func:`~bidslab.io.write_dataset`
        Write a dataset to disk.

    Notes
    -----
    Dataset loading uses lazy loading to minimize memory overhead.
    Entities are discovered automatically from the BIDS hierarchy.

    Examples
    --------
    >>> from bidslab import load_dataset
    >>> dataset = load_dataset("path/to/dataset")  # doctest: +SKIP
    >>> dataset.subjects
    ['sub-01', 'sub-02']
    """
```

## Validation Workflow

Before committing documentation changes:

1. **Run Ruff checks**:

   ```bash
   python -m ruff check --select D src/bidslab/
   ```

   Expected: "All checks passed!"

1. **Run numpydoc lint**:

   ```bash
   python -m numpydoc lint ./src/bidslab/**/*.py
   ```

   Expected: No errors

1. **Verify Python compilation**:

   ```bash
   python -m py_compile src/bidslab/module.py
   ```

   Expected: No errors

1. **Build Sphinx documentation**:

   ```bash
   python -m sphinx -b html docs/source docs/build/html
   ```

   Expected: "build succeeded, XXX warnings"

1. **Spot-check HTML output**:

   - Verify docs/build/html/ is created
   - Check that cross-references are functional
   - Verify code examples render correctly

## Special Considerations

### Lazy Loading Documentation

- Clearly document which entities use lazy loading
- Explain performance implications
- Show when data is actually loaded
- Include memory overhead notes

### BIDS Compliance Documentation

- Reference relevant BIDS specification sections
- Document entity naming conventions
- Explain hierarchy constraints
- Provide valid entity value examples

## Agent Guidelines

When enhancing documentation:

1. **Always maintain consistency** with existing documented classes
1. **Follow the section order** strictly (Summary → Parameters → Returns → etc.)
1. **Use proper cross-references** with tilde (~) notation
1. **Include practical examples** for user-facing classes/functions
1. **Document all parameters** including optional ones
1. **Validate with Ruff and numpydoc** before considering work complete
1. **Build Sphinx** to verify rendering

## References

- [NumPy Docstring Guide](https://numpydoc.readthedocs.io/en/latest/format.html)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Napoleon Extension](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)
- [Ruff Documentation Rules](https://docs.astral.sh/ruff/rules/#pydocstyle-d)
- [BIDS Specification](https://bids-standard.github.io/bids-standard/)
