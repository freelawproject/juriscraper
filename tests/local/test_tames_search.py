"""Tests for TAMES search result parsing."""

import unittest

from lxml import html

from juriscraper.state.texas.tames import TAMESScraper
from tests import TESTS_ROOT_EXAMPLES_STATES


class TamesSearchParseTest(unittest.TestCase):
    """Test parsing of TAMES search result pages."""

    def setUp(self):
        self.maxDiff = 200000
        self.scraper = TAMESScraper()

    def test_parse_search_results(self):
        """Test parsing search results from CaseSearch.aspx.html fixture."""
        fixture_path = (
            TESTS_ROOT_EXAMPLES_STATES / "texas" / "CaseSearch.aspx.html"
        )
        with open(fixture_path, "rb") as f:
            content = f.read()

        tree = html.fromstring(content)
        results = list(self.scraper._parse_search_results(tree))

        # Should have 6 results based on the fixture
        self.assertEqual(len(results), 6)

        # Verify first result
        first = results[0]
        self.assertIsInstance(first, dict)
        self.assertEqual(first["case_number"], "01-00-00288-CV")
        self.assertEqual(
            first["case_url"],
            "https://search.txcourts.gov/Case.aspx?cn=01-00-00288-CV&coa=coa01",
        )
        self.assertEqual(first["date_filed"], "1/1/2000")
        self.assertEqual(first["style"], "Green Tree at the Gardens")
        self.assertEqual(first["v"], "Hoechst Celanese Corp., et al")
        self.assertEqual(first["case_type"], "Miscellaneous/other civil")
        self.assertEqual(first["coa_case_number"], "")
        self.assertEqual(first["trial_court_case_number"], "94019534A")
        self.assertEqual(first["trial_court_county"], "Harris")
        self.assertEqual(first["trial_court"], "281st District Court")
        self.assertEqual(first["appellate_court"], "COA01")
        self.assertEqual(first["court_code"], "coa01")

        # Verify second result
        second = results[1]
        self.assertEqual(second["case_number"], "01-00-00289-CV")
        self.assertEqual(
            second["style"], "Kenneth W. and Patsy E. Dunn, et al.,"
        )
        self.assertEqual(second["trial_court_case_number"], "9407179A")
        self.assertEqual(second["trial_court"], "189th District Court")

        # Verify criminal case (fourth result)
        criminal = results[3]
        self.assertEqual(criminal["case_number"], "01-00-00489-CR")
        self.assertEqual(criminal["style"], "Jones, Theron")
        self.assertEqual(criminal["v"], "The State of Texas")
        self.assertEqual(criminal["case_type"], "Aggravated Sexual Assault")
        self.assertEqual(criminal["trial_court_case_number"], "33793")
        self.assertEqual(criminal["trial_court_county"], "Brazoria")

        # Verify different COA (fifth result)
        coa06 = results[4]
        self.assertEqual(coa06["case_number"], "06-00-00152-CV")
        self.assertEqual(coa06["appellate_court"], "COA06")
        self.assertEqual(coa06["court_code"], "coa06")
        self.assertEqual(coa06["case_type"], "Divorce")

        # Verify CCA case (sixth result)
        cca = results[5]
        self.assertEqual(cca["case_number"], "WR-90,443-02")
        self.assertEqual(cca["appellate_court"], "CCA")
        self.assertEqual(cca["court_code"], "coscca")
        self.assertEqual(cca["case_type"], "11.07 HC")

    def test_parse_search_results_handles_empty_cells(self):
        """Test that empty cells (with &nbsp;) are handled correctly."""
        fixture_path = (
            TESTS_ROOT_EXAMPLES_STATES / "texas" / "CaseSearch.aspx.html"
        )
        with open(fixture_path, "rb") as f:
            content = f.read()

        tree = html.fromstring(content)
        results = list(self.scraper._parse_search_results(tree))

        # The CCA case has empty trial court fields
        cca = results[5]
        self.assertEqual(cca["trial_court_case_number"], "")
        self.assertEqual(cca["trial_court_county"], "")
        self.assertEqual(cca["trial_court"], "")

    def test_has_next_page_returns_false_on_last_page(self):
        """Test that _has_next_page returns False on the last page of results."""
        fixture_path = (
            TESTS_ROOT_EXAMPLES_STATES
            / "texas"
            / "CaseSearch_LastPage.aspx.html"
        )
        with open(fixture_path, "rb") as f:
            content = f.read()

        tree = html.fromstring(content)

        # This fixture is page 40 of 40 (last page)
        self.assertFalse(self.scraper._has_next_page(tree))

        # Verify the page has results (not an empty page)
        results = list(self.scraper._parse_search_results(tree))
        self.assertGreater(len(results), 0)

    def test_has_next_page_returns_true_on_middle_page(self):
        """Test that _has_next_page returns True when more pages exist."""
        fixture_path = (
            TESTS_ROOT_EXAMPLES_STATES
            / "texas"
            / "CaseSearch_MiddlePage.aspx.html"
        )
        with open(fixture_path, "rb") as f:
            content = f.read()

        tree = html.fromstring(content)

        # This fixture is page 9 of 40 (middle page)
        self.assertTrue(self.scraper._has_next_page(tree))


if __name__ == "__main__":
    unittest.main()
