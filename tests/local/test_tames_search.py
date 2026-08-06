"""Tests for TAMES search result parsing."""

import unittest
from datetime import date

from lxml import html

from juriscraper.state.texas.tames import (
    ATTORNEY_BAR_FIELD,
    BLANK_CRITERIA_FIELDS,
    TAMESScraper,
)
from tests import TESTS_ROOT_EXAMPLES_STATES


def _search_page(bar_value: str = "", rows: int = 0, items: int = 0) -> bytes:
    """Minimal stand-in for a TAMES search/results page."""
    info = (
        f'<div class="rgWrap rgInfoPart">{items} items in 1 pages</div>'
        if items
        else ""
    )
    body = "".join(
        f'<tr class="rgRow">'
        f'<td><a href="/Case.aspx?cn=X-{i}&coa=coa01">X-{i}</a></td>'
        f"<td>6/2/2026</td>" + "<td>c</td>" * 8 + "<td>coa01</td></tr>"
        for i in range(rows)
    )
    return (
        "<html><body><form>"
        '<input type="hidden" name="__VIEWSTATE" value="vs" />'
        f'<input name="{ATTORNEY_BAR_FIELD}" type="text" value="{bar_value}" />'
        f"{info}"
        f'<table id="ctl00_ContentPlaceHolder1_grdCases_ctl00">{body}</table>'
        "</form></body></html>"
    ).encode()


class FakeResponse:
    def __init__(self, content: bytes):
        self.content = content
        self.status_code = 200

    def raise_for_status(self):
        pass


class FakeRequestManager:
    """Serves canned form/results pages and records what was posted."""

    def __init__(self, form_pages: list[bytes], result_pages: list[bytes]):
        self._form_pages = form_pages
        self._result_pages = result_pages
        self.posted_bodies: list[dict[str, str]] = []
        self.get_count = 0

    def get(self, url, **kwargs):
        page = self._form_pages[min(self.get_count, len(self._form_pages) - 1)]
        self.get_count += 1
        return FakeResponse(page)

    def post(self, url, data=None, **kwargs):
        page = self._result_pages[
            min(len(self.posted_bodies), len(self._result_pages) - 1)
        ]
        self.posted_bodies.append(data or {})
        return FakeResponse(page)


class TamesBarNumberTest(unittest.TestCase):
    """TAMES injects bar numbers into the search form.

    Left in place, an injected value survives in __VIEWSTATE and filters the whole
    search down to one attorney, so a populated date range comes back with only
    that attorney's cases — often zero rows, but not always.
    """

    def _scraper(self, form_pages, result_pages):
        rm = FakeRequestManager(form_pages, result_pages)
        scraper = TAMESScraper()
        scraper.request_manager = rm
        return scraper, rm

    def test_bar_number_always_posted_blank(self):
        """Every search posts the attorney field, explicitly blank."""
        scraper, rm = self._scraper(
            [_search_page()], [_search_page(rows=2, items=2)]
        )

        gen = scraper._submit_search(date(2026, 6, 1), date(2026, 6, 2))
        result_count = next(gen)
        rows = list(gen)

        self.assertEqual(result_count, 2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rm.posted_bodies), 1)
        for field in BLANK_CRITERIA_FIELDS:
            self.assertIn(field, rm.posted_bodies[0])
            self.assertEqual(rm.posted_bodies[0][field], "")

    def test_zero_rows_with_prefilled_bar_number_is_retried(self):
        """A poisoned form plus zero rows triggers one clean resubmission."""
        scraper, rm = self._scraper(
            # First form arrives poisoned, the second one is clean
            [_search_page("24075665"), _search_page()],
            # First search comes back filtered/empty, the retry finds rows
            [_search_page("24075665"), _search_page(rows=2, items=2)],
        )

        gen = scraper._submit_search(date(2026, 6, 1), date(2026, 6, 2))
        result_count = next(gen)
        rows = list(gen)

        self.assertEqual(rm.get_count, 2)
        self.assertEqual(len(rm.posted_bodies), 2)
        self.assertEqual(result_count, 2)
        self.assertEqual(len(rows), 2)
        for body in rm.posted_bodies:
            self.assertEqual(body[ATTORNEY_BAR_FIELD], "")

    def test_nonzero_rows_with_prefilled_bar_number_is_retried(self):
        """An injected bar number belonging to an attorney with cases.

        The filtered search returns rows, so row count can't be the signal --
        only the bar number echoed back on the results page can.
        """
        scraper, rm = self._scraper(
            [_search_page("24075665"), _search_page()],
            # The injected attorney has 3 cases in the window; the clean retry
            # finds the 7 that are really there
            [
                _search_page("24075665", rows=3, items=3),
                _search_page(rows=7, items=7),
            ],
        )

        with self.assertLogs("juriscraper", level="WARNING") as logs:
            gen = scraper._submit_search(date(2026, 6, 1), date(2026, 6, 2))
            result_count = next(gen)
            rows = list(gen)

        self.assertEqual(len(rm.posted_bodies), 2)
        self.assertEqual(result_count, 7)
        self.assertEqual(len(rows), 7)
        self.assertTrue(
            any("resubmitting" in line for line in logs.output),
            f"expected a resubmission warning, got {logs.output}",
        )

    def test_persistent_bar_number_with_rows_is_logged_as_an_error(self):
        """A retry that stays filtered is flagged however many rows it has."""
        scraper, _ = self._scraper(
            [_search_page("24075665")],
            [_search_page("24075665", rows=3, items=3)],
        )

        with self.assertLogs("juriscraper", level="ERROR") as logs:
            gen = scraper._submit_search(date(2026, 6, 1), date(2026, 6, 2))
            self.assertEqual(next(gen), 3)
            list(gen)

        self.assertTrue(
            any("can't be trusted" in line for line in logs.output),
            f"expected an untrusted-results error, got {logs.output}",
        )

    def test_genuinely_empty_result_is_not_retried(self):
        """A clean form with no matches is a real answer, not a retry."""
        scraper, rm = self._scraper([_search_page()], [_search_page()])

        gen = scraper._submit_search(date(2026, 6, 1), date(2026, 6, 2))
        result_count = next(gen)
        rows = list(gen)

        self.assertEqual(result_count, 0)
        self.assertEqual(rows, [])
        self.assertEqual(len(rm.posted_bodies), 1)

    def test_pagination_keeps_the_bar_number_blank(self):
        """Page 2+ must not re-poison the search."""
        scraper, _ = self._scraper([_search_page()], [_search_page()])
        form_data = scraper._build_form_data(
            date(2026, 6, 1), date(2026, 6, 2)
        )

        self.assertEqual(form_data[ATTORNEY_BAR_FIELD], "")

        tree = html.fromstring(
            '<html><body><input class="rgPageNext" name="next" value="1" />'
            "</body></html>"
        )
        scraper._fetch_next_page(tree, form_data)
        # _fetch_next_page posts through the same manager
        self.assertEqual(
            scraper.request_manager.posted_bodies[-1][ATTORNEY_BAR_FIELD], ""
        )

    def test_bar_number_value_reads_prefilled_form(self):
        clean = html.fromstring(_search_page())
        poisoned = html.fromstring(_search_page("24075665"))

        self.assertEqual(TAMESScraper._bar_number_value(clean), "")
        self.assertEqual(TAMESScraper._bar_number_value(poisoned), "24075665")

    def test_real_form_fixture_is_clean(self):
        """The checked-in fixture shows the normal, unpoisoned form."""
        fixture_path = (
            TESTS_ROOT_EXAMPLES_STATES / "texas" / "CaseSearch.aspx.html"
        )
        with open(fixture_path, "rb") as f:
            tree = html.fromstring(f.read())

        self.assertEqual(TAMESScraper._bar_number_value(tree), "")


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
