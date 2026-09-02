#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause


class FieldEntryNotValidError(Exception):
    """Raised when a field entry is not valid."""

    pass


class FieldMissingError(Exception):
    """Raised when a required field is missing."""

    pass


class FieldMissingWarning(Warning):
    """Raised when a recommended field is missing."""

    pass


class FieldNotValidError(Exception):
    """Raised when a field is not valid."""

    pass


class FieldPresentError(Exception):
    """Raised when a field is present, but not allowed."""

    pass


class FieldPresentWarning(Warning):
    """Raised when a field is present, but should not be present."""

    pass


class FileMissingError(Exception):
    """Raised when a required file is missing."""

    pass


class FileMissingWarning(Warning):
    """Raised when a recommended file is missing."""

    pass


class FileNotFoundWarning(Warning):
    """Raised when a file is not found."""

    pass


class FileTypeUnsupportedWarning(Warning):
    """Raised when a file type is unsupported."""

    pass


class InvalidURIError(Exception):
    """Raised when a URI is not valid."""

    pass


class MultipleFilesFoundError(Exception):
    """Raised when multiple files are found, but only one is allowed."""

    pass


class MultipleFilesFoundWarning(Warning):
    """Raised when multiple files are found, but only one is expected."""

    pass


class PathsSameWarning(Warning):
    """Raised when two paths are the same."""

    pass


class TopLevelEntityNotLinkedWarning(Warning):
    """Raised when a top-level entity is not linked."""

    pass


class VersionMismatchError(Exception):
    """Raised when two versions are not the same."""

    pass


class VersionMismatchWarning(Warning):
    """Raised when two versions are not the same."""

    pass
