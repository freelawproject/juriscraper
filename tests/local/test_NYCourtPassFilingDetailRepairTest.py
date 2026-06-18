#!/usr/bin/env python
"""Tests for the Court-PASS ``<style pdffontname>`` HTML repair.

The filing-detail steps repair the raw response text before lxml parses
it (see ``repair_pdffont_leakage``); the parser then assumes a clean DOM.
This exercises that repair directly against a real leaked capture, which
the parser-example harness never sees: ``leaked_with_recoverable_files``
is committed in its *repaired* shape as the ``.html`` fixture, while the
original swallowing capture is kept beside it as ``.rawhtml``.
"""

import unittest

from lxml import html as lxml_html

from juriscraper.state.new_york.nycourts_gov.parsers._common import (
    repair_pdffont_leakage,
)
from tests import TESTS_ROOT_EXAMPLES

_FIXTURES = (
    TESTS_ROOT_EXAMPLES
    / "state"
    / "new_york"
    / "nycourts_gov"
    / "FilingDetailParser"
)
_GVFILES = "//table[contains(@id, 'gvFiles')]"
_FILE_ROWS = _GVFILES + "//tr[position()>1]"
_ISSUE_P = "//p[contains(@class, 'case-issues-text')]"


class NYCourtPassFilingDetailRepairTest(unittest.TestCase):
    """Compare the parsed tree before and after the pdffont-leak repair."""

    @classmethod
    def setUpClass(cls):
        # The raw capture carries the unclosed ``<style pdffontname>``;
        # read bytes (lossless via latin-1) so the repaired string can be
        # compared byte-for-byte against the committed ``.html`` fixture.
        cls.raw_bytes = (
            _FIXTURES / "leaked_with_recoverable_files.rawhtml"
        ).read_bytes()
        cls.repaired = repair_pdffont_leakage(cls.raw_bytes.decode("latin-1"))
        cls.before = lxml_html.fromstring(cls.raw_bytes)
        cls.after = lxml_html.fromstring(cls.repaired)

    def test_raw_capture_actually_leaks(self):
        """Guard the premise: unrepaired, the bogus style swallows the page.

        lxml treats the unclosed ``<style pdffontname>`` as raw text running
        to end-of-document, so the gvFiles table vanishes from the tree and
        the issue ``<p>`` absorbs the rest of the page (down to ``</html>``).
        """
        self.assertIn("pdffontname", self.raw_bytes.decode("latin-1"))
        self.assertEqual([], self.before.xpath(_GVFILES))
        self.assertEqual([], self.before.xpath(_FILE_ROWS))
        issue_text = self.before.xpath(_ISSUE_P)[0].text_content()
        self.assertIn("</html>", issue_text)

    def test_repair_restores_the_tree(self):
        """After repair the swallowed structure is back in the DOM."""
        self.assertNotIn("pdffontname", self.repaired)
        self.assertEqual(1, len(self.after.xpath(_GVFILES)))
        self.assertEqual(9, len(self.after.xpath(_FILE_ROWS)))
        issue_text = self.after.xpath(_ISSUE_P)[0].text_content().strip()
        self.assertNotIn("</", issue_text)
        self.assertTrue(
            issue_text.endswith("People v Rudolph (21 NY3d 497 [2013]).")
        )

    def test_repair_is_byte_identical_to_committed_fixture(self):
        """The repair output is exactly the shape handed to the parser.

        The committed ``.html`` fixture is the parser's input; it must be
        what ``repair_pdffont_leakage`` produces from the raw capture, or
        the parser tests and the live pipeline would diverge.
        """
        committed = (
            _FIXTURES / "leaked_with_recoverable_files.html"
        ).read_bytes()
        self.assertEqual(committed, self.repaired.encode("latin-1"))

    def test_repair_is_a_noop_without_the_marker(self):
        """Pages without the bogus marker pass through untouched."""
        clean = "<html><body><p>no marker here</p></body></html>"
        self.assertEqual(clean, repair_pdffont_leakage(clean))


if __name__ == "__main__":
    unittest.main()
