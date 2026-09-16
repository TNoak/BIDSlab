#  Copyright (c) 2026 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

from sphinx.ext import autodoc

sys.path.insert(0, os.path.abspath("../../src"))

project = "BIDSlab"
copyright = "2025, Lukas Behammer"
author = "Lukas Behammer"

with open("../../src/bidslab/__init__.py") as f:
    setup_lines = f.readlines()
version = "vUndefined"
for line in setup_lines:
    if line.startswith("__version__"):
        version = line.split('"')[1]
        break

release = version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "sphinx.ext.autosummary",
    "numpydoc",
    "sphinxcontrib.email",
    "sphinx_copybutton",
    "sphinx_last_updated_by_git",
    "pytest_doctestplus.sphinx.doctestplus",
]

# templates_path = ["_templates"]
exclude_patterns = ["typing.rst"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
# html_static_path = ["_static"]
# html_favicon = '../../branding/logo/Logo_aBIDSkit_wo-text.svg'
html_title = f"{project} documentation v{release}"

# -- Options for Autodoc -----------------------------------------------------

###############################################
# Source - https://stackoverflow.com/a/79492670
# Posted by jxrossel
# Retrieved 2026-01-12, License - CC BY-SA 4.0

autodoc.Documenter.member_order = 0
autodoc.DataDocumenter.member_order = 10
autodoc.FunctionDocumenter.member_order = 20
autodoc.ClassDocumenter.member_order = 30
autodoc.AttributeDocumenter.member_order = 40
autodoc.PropertyDocumenter.member_order = 40
autodoc.MethodDocumenter.member_order = 50
autodoc.ExceptionDocumenter.member_order = 60
###############################################

autodoc_member_order = "groupwise"
autodoc_default_options = {
    "members": None,
    # "member-order": "bysource",
    # "exclude-members": "__init__",
    # "inherited-members": None,
}

# -- Options for Napoleon -----------------------------------------------------
napoleon_google_docstring = False
napoleon_use_admonition_for_notes = True
napoleon_use_rtype = False
napoleon_preprocess_types = True
napoleon_type_aliases = {
    "A": "Object",
    "E": "Object",
    "R": "Object",
    "T": "Object",
}

# -- Options for Todo ---------------------------------------------------------
todo_include_todos = True
todo_link_only = True

# -- Options for Numpydoc -----------------------------------------------------
numpydoc_show_inherited_class_members = False
numpydoc_attributes_as_param_list = True
numpydoc_validation_checks = {"all", "EX01", "SA01", "ES01"}
numpydoc_validation_exclude = {
    "\\.__repr__$",
}

# -- Options for Coverage -----------------------------------------------------
coverage_modules = ["bidslab"]
coverage_statistics_to_stdout = True
