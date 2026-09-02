#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

import itertools

import pytest
from mimesis import Development, Fieldset, Numeric, Text

import bidslab as abk
from tests.conftest import delete_files, make_files, make_mock_files

EXTENSIONS = ["", ".md", ".txt", ".rst"]


class TestDescription:
    def test_description_present(self, test_dataset, tmp_root):
        # Setup
        make_files(tmp_root, ["dataset_description.json"])
        # Test
        assert test_dataset.root == tmp_root
        try:
            abk.utils.checks.check_dataset_description_present(test_dataset)
        except Warning as e:
            pytest.fail(f"Unexpected warning raised: {e}")
        # Teardown
        delete_files(tmp_root, ["dataset_description.json"])

    def test_description_missing(self, test_dataset, tmp_root):
        # Setup
        make_files(tmp_root, ["README", "CHANGES"])
        # Test
        assert test_dataset.root == tmp_root
        assert not (tmp_root / "dataset_description.json").exists()
        with pytest.raises(abk.utils.exceptions.FileMissingError):
            abk.utils.checks.check_dataset_description_present(test_dataset)
        # Teardown
        delete_files(tmp_root, ["README", "CHANGES"])


class TestREADME:
    @pytest.mark.parametrize(
        "files",
        [["CHANGES", "README" + ext] for ext in EXTENSIONS],
    )
    def test_readme_present(self, test_dataset, tmp_root, files):
        # Setup
        files = make_mock_files(tmp_root, files)
        # Test
        assert test_dataset.readme_path is None
        try:
            abk.utils.checks.check_readme(test_dataset, files)
        except abk.utils.exceptions.FileMissingError:
            pytest.fail("FileMissingError raised unexpectedly!")
        assert test_dataset.readme_path in [
            (tmp_root / "README").with_suffix(ext) for ext in EXTENSIONS
        ]

    def test_readme_missing(self, test_dataset, tmp_root):
        # Setup
        files = make_mock_files(tmp_root, ["CHANGES", "CITATION.cff"])
        # Test
        assert test_dataset.readme_path is None
        with pytest.raises(abk.utils.exceptions.FileMissingError):
            abk.utils.checks.check_readme(test_dataset, files)

    def test_readme_multiple(self, test_dataset, tmp_root):
        # Setup
        files = make_mock_files(tmp_root, ["README", "README.md"])
        # Test
        assert test_dataset.readme_path is None
        with pytest.raises(abk.utils.exceptions.MultipleFilesFoundError):
            abk.utils.checks.check_readme(test_dataset, files)


class TestCITATION:
    def test_citation_file_present(self, test_dataset, tmp_root):
        # Setup
        files = make_mock_files(tmp_root, ["README", "CITATION.cff"])
        test_dataset.authors = None
        # Test
        assert test_dataset.citation_path is None
        try:
            abk.utils.checks.check_citation(test_dataset, files)
        except Warning as e:
            pytest.fail(f"Unexpected warning raised: {e}")
        assert test_dataset.citation_path == tmp_root / "CITATION.cff"

    def test_citation_file_missing(self, test_dataset, tmp_root):
        # Setup
        files = make_mock_files(tmp_root, ["README", "CHANGES"])
        # Test
        assert test_dataset.citation_path is None
        try:
            abk.utils.checks.check_citation(test_dataset, files)
        except Warning as e:
            pytest.fail(f"Unexpected warning raised: {e}")
        assert test_dataset.citation_path is None

    def test_citation_with_authors(self, test_dataset, tmp_root):
        # Setup
        files = make_mock_files(tmp_root, ["README", "CITATION.cff"])
        test_dataset.authors = Fieldset()(
            "person.full_name", i=Numeric().integer_number(1, 10)
        )
        # Test
        with pytest.raises(abk.utils.exceptions.FieldPresentError):
            abk.utils.checks.check_citation(test_dataset, files)

    @pytest.mark.parametrize(
        ("files", "attribute"),
        itertools.zip_longest(
            [],
            ["how_to_acknowledge", "license", "references_and_links"],
            fillvalue=["CITATION.cff"],
        ),
    )
    def test_citation_with_fields(self, test_dataset, tmp_root, files, attribute):
        # Setup
        files = make_mock_files(tmp_root, files)
        setattr(test_dataset, attribute, Text().sentence())
        # Test
        with pytest.warns(abk.utils.exceptions.FieldPresentWarning):
            abk.utils.checks.check_citation(test_dataset, files)


class TestLicense:
    @pytest.mark.parametrize(
        "files",
        [["README", "LICENSE" + ext] for ext in EXTENSIONS],
    )
    def test_license_file_present(self, test_dataset, tmp_root, files):
        # Setup
        files = make_mock_files(tmp_root, files)
        test_dataset.license = Development().software_license()
        # Test
        assert test_dataset.license_path is None
        try:
            abk.utils.checks.check_license(test_dataset, files)
        except Warning as e:
            pytest.fail(f"Unexpected warning raised: {e}")
        assert test_dataset.license_path in [
            (tmp_root / "LICENSE").with_suffix(ext) for ext in EXTENSIONS
        ]

    def test_license_file_missing(self, test_dataset, tmp_root):
        # Setup
        files = make_mock_files(tmp_root, ["README", "CHANGES"])
        test_dataset.license = Development().software_license()
        # Test
        assert test_dataset.license_path is None
        try:
            abk.utils.checks.check_license(test_dataset, files)
        except Warning as e:
            pytest.fail(f"Unexpected warning raised: {e}")
        assert test_dataset.license_path is None

    @pytest.mark.parametrize(
        "files",
        [["README", "LICENSE" + ext] for ext in EXTENSIONS],
    )
    def test_license_file_without_license_field(self, test_dataset, tmp_root, files):
        # Setup
        files = make_mock_files(tmp_root, files)
        # Test
        assert test_dataset.license is None
        with pytest.warns(abk.utils.exceptions.FieldMissingWarning):
            abk.utils.checks.check_license(test_dataset, files)
