# pip requirements files

## Overview

The files in this directory are pinned requirement lists generated with
[uv](https://docs.astral.sh/uv/) from the dependency declarations in
`pyproject.toml`. Do not edit them by hand; change `pyproject.toml` and
regenerate instead.

Each file lists the resolved versions of the packages it needs, annotated with
the origin of each entry (`# via bidslab (pyproject.toml:<group>)`).

## Regenerating the files

The files are regenerated automatically by the `generate_requirements`
pre-commit hook whenever `pyproject.toml` changes. The hook runs
the `uv pip compile` commands defined in `.pre-commit-config.yaml`:

```bash
$ pre-commit run generate_requirements --all-files
```

The `generate-requirements` tox environment in `tox.ini` runs the same
commands and can be used as an alternative:

```bash
$ tox -e generate-requirements
```

Keep the two command lists in sync when adding or removing requirement files.

## Index

- [default.txt](default.txt)
  Runtime dependencies of the package (`[project] dependencies`).
- [extra.txt](extra.txt)
  Runtime dependencies plus all optional extras (`datalad`).
- [test.txt](test.txt)
  Requirements for running the test suite (`test` dependency group).
- [docs.txt](docs.txt)
  Requirements for building the documentation (`docs` dependency group).
- [lint.txt](lint.txt)
  Linting and formatting requirements (`lint` dependency group).
- [typing.txt](typing.txt)
  Static type checking requirements (`typing` dependency group).
- [build.txt](build.txt)
  Requirements for building source and wheel distributions (`build` dependency group).
- [release.txt](release.txt)
  Requirements for releasing the package (`release` dependency group).
- [tox.txt](tox.txt)
  Requirements for running tox (`tox` dependency group).
- [dev.txt](dev.txt)
  Full developer environment, combining all dependency groups and `pre-commit`.

## Examples

### Installing the runtime requirements

```bash
$ pip install -U -r requirements/default.txt
```

### Installing the optional extras

```bash
$ pip install -U -r requirements/extra.txt
```

### Running the tests

```bash
$ pip install -U -e . -r requirements/test.txt
$ pytest tests
```

### Setting up a developer environment

```bash
$ pip install -U -e . -r requirements/dev.txt
$ pre-commit install
```
