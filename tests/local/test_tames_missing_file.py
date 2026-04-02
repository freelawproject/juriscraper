"""Tests for TAMES missing file page detection."""

import unittest

from juriscraper.state.texas.missing_file import is_missing_file_page
from tests import TESTS_ROOT_EXAMPLES_STATES


class TamesMissingFileTest(unittest.TestCase):
    """Test detection of TAMES 'File not found' error pages."""

    def test_missing_file_page_detected(self):
        """Verify a TAMES 'File not found' page is correctly identified."""
        fixture_path = (
            TESTS_ROOT_EXAMPLES_STATES / "texas" / "missing_file.html"
        )
        with open(fixture_path, "rb") as f:
            self.assertTrue(is_missing_file_page(f.read()))

    def test_normal_page_not_flagged(self):
        """Verify a normal TAMES docket page is not flagged as missing."""
        fixture_path = (
            TESTS_ROOT_EXAMPLES_STATES
            / "texas"
            / "coa"
            / "01-25-00011-CV.html"
        )
        with open(fixture_path, "rb") as f:
            self.assertFalse(is_missing_file_page(f.read()))


if __name__ == "__main__":
    unittest.main()
