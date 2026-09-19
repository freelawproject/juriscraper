"""Tests for the Los Angeles Superior Court case summary parsers."""

import unittest
from datetime import date

from juriscraper.abstract_parser import ParserValidationError
from juriscraper.state.california.lasc.case_summary import (
    CaseSummaryParser,
    LASCCaseSummary,
    build_case_search_form_data,
    restricted_case_message,
    search_result_message,
)
from juriscraper.state.docket import DocketEntryType
from tests import TESTS_ROOT_EXAMPLES_STATES
from tests.local.PacerParseTestCase import PacerParseTestCase

EXAMPLES = TESTS_ROOT_EXAMPLES_STATES / "california" / "lasc" / "case_summary"


def _table(*rows: tuple[str, ...]) -> str:
    """Build a `dataTable` the way the case summary prints one."""
    body = "".join(
        "<tr>"
        + "".join(
            f'<td class="KeyField">{cell}</td>'
            if i == 0
            else f"<td>{cell}</td>"
            for i, cell in enumerate(row)
        )
        + "</tr>"
        for row in rows
    )
    return f'<table class="dataTable">{body}</table>'


def _page(**sections: str) -> str:
    """Build a case summary page from section tables keyed by anchor name.

    The case information section is filled in unless it is given.
    """
    sections.setdefault(
        "CaseInformation",
        _table(
            ("CASE INFORMATION:", "25STCV20242"),
            ("Case Title:", "JIMENEZ VS 33 TAPS, LLC"),
            ("Filing Courthouse:", "Stanley Mosk Courthouse"),
            ("Filing Date:", "7/9/2025"),
            ("Case Type:", "Premise Liability (General Jurisdiction)"),
            ("Status:", "Pending"),
        ),
    )
    body = "".join(
        f'<a name="{name}"></a><div class="caseInfoHeader">{name}</div>{table}'
        for name, table in sections.items()
    )
    return f"<html><body>{body}</body></html>"


class LASCCaseSummaryExampleTest(PacerParseTestCase):
    """Parse the case summaries captured from the court's site."""

    def setUp(self) -> None:
        self.maxDiff = 200000

    def test_case_summaries(self) -> None:
        self.parse_files(
            EXAMPLES, "lasc_case_summary_*.html", CaseSummaryParser
        )


class LASCCaseSummaryParserTest(unittest.TestCase):
    """Edge cases of reading a case summary."""

    def parse(self, page: str) -> LASCCaseSummary:
        parser = CaseSummaryParser("lasc")
        parser._parse_text(page)
        return parser.data

    def test_case_information(self) -> None:
        case = self.parse(_page())
        self.assertEqual(case.docket_number, "25STCV20242")
        self.assertEqual(case.case_name_full, "JIMENEZ VS 33 TAPS, LLC")
        self.assertEqual(case.date_filed, date(2025, 7, 9))
        self.assertEqual(case.courthouse, "Stanley Mosk Courthouse")
        self.assertEqual(case.status, "Pending")

    def test_page_without_case_information_fails(self) -> None:
        with self.assertRaises(ParserValidationError):
            self.parse(_page(CaseInformation=_table(("Status:", "Pending"))))

    def test_documents_filed(self) -> None:
        case = self.parse(
            _page(
                DocumentsFiled=_table(
                    (
                        "1/30/2026",
                        "Minute Order\n (Non-Appearance Case Review)",
                        "Filed by Clerk",
                    ),
                    (
                        "7/9/2025",
                        "Summons\non Complaint",
                        "Filed by Sandra Jimenez (Plaintiff)",
                    ),
                    (
                        "9/17/2025",
                        "Notice of Motion",
                        "Filed by 33 Taps, LLC (Defendant)",
                    ),
                )
            )
        )
        order, summons, motion = case.entries
        self.assertEqual(order.document_type, "Minute Order")
        self.assertEqual(order.description, "Non-Appearance Case Review")
        self.assertEqual(order.filed_by, "Clerk")
        self.assertIsNone(order.filed_by_role)
        self.assertEqual(order.entry_type, DocketEntryType.ORDER)
        self.assertEqual(summons.description, "on Complaint")
        self.assertEqual(summons.filed_by, "Sandra Jimenez")
        self.assertEqual(summons.filed_by_role, "Plaintiff")
        self.assertEqual(motion.filed_by, "33 Taps, LLC")
        self.assertEqual(motion.entry_type, DocketEntryType.MOTION)

    def test_attorneys_join_only_an_unambiguous_party(self) -> None:
        case = self.parse(
            _page(
                Parties=_table(
                    ("33 TAPS LLC", "Defendant"),
                    ("CRANERT TERRENCE L.", "Attorney for Defendant"),
                    ("EISENBERG JASON", "Attorney for Plaintiff"),
                    ("FLOYD RYAN", "Defendant"),
                    ("JIMENEZ SANDRA", "Plaintiff"),
                )
            )
        )
        parties = {party.name: party for party in case.parties}
        self.assertEqual(
            [r.name for r in parties["JIMENEZ SANDRA"].representatives],
            ["EISENBERG JASON"],
        )
        self.assertEqual(parties["33 TAPS LLC"].representatives, [])
        self.assertEqual(parties["FLOYD RYAN"].role, "Defendant")
        self.assertEqual(len(case.attorneys), 2)

    def test_hearings(self) -> None:
        case = self.parse(
            _page(
                FutureHearings=_table(
                    (
                        "11/2/2027",
                        "08:30",
                        "Department  514",
                        "111 North Hill Street, Los Angeles, CA 90012",
                        "Final Status Conference",
                    )
                ),
                PastProceedings=_table(
                    (
                        "1/30/2026 10:30 AM",
                        "Department  56",
                        "Case Review",
                        "Held",
                    )
                ),
            )
        )
        upcoming, held = case.hearings
        self.assertTrue(upcoming.upcoming)
        self.assertEqual(upcoming.department, "514")
        self.assertEqual(upcoming.event, "Final Status Conference")
        self.assertFalse(held.upcoming)
        self.assertEqual(held.hearing_date, date(2026, 1, 30))
        self.assertEqual(held.time, "10:30 AM")
        self.assertEqual(held.result, "Held")

    def test_section_without_table_borrows_nothing(self) -> None:
        page = _page(
            FutureHearings="", Parties=_table(("JIMENEZ SANDRA", "Plaintiff"))
        )
        case = self.parse(page)
        self.assertEqual(case.hearings, [])
        self.assertEqual(
            [party.name for party in case.parties], ["JIMENEZ SANDRA"]
        )


class LASCCaseSummarySearchTest(unittest.TestCase):
    """Posting a search and reading its outcome."""

    def setUp(self) -> None:
        with open(EXAMPLES / "search_not_found_25STCV99998.html") as f:
            self.not_found = f.read()

    def test_not_found_message(self) -> None:
        self.assertEqual(
            search_result_message(self.not_found),
            "No match found for case number 25STCV99998.",
        )
        with open(EXAMPLES / "lasc_case_summary_25STCV20242.html") as f:
            self.assertIsNone(search_result_message(f.read()))

    def test_search_form_data(self) -> None:
        data = build_case_search_form_data(self.not_found, "25STCV20242")
        self.assertEqual(data["txtCaseNumber"], "25STCV20242")
        self.assertEqual(data["action"], "Search")
        self.assertTrue(data["__RequestVerificationToken"])

    def test_search_form_data_without_form(self) -> None:
        with self.assertRaises(ValueError):
            build_case_search_form_data("<html><body></body></html>", "x")

    def test_restricted_case_notice(self) -> None:
        """A confidential case's notice is recognized; a summary isn't."""
        with open(EXAMPLES / "restricted_26STCV00002.html") as f:
            restricted = f.read()
        self.assertEqual(
            restricted_case_message(restricted),
            "Case Number 26STCV00002 is a confidential Unlawful Detainer case.",
        )
        self.assertEqual(
            search_result_message(restricted),
            "You are not authorized to view this case. Please validate your "
            "authorization.",
        )
        with open(EXAMPLES / "lasc_case_summary_25STCV20242.html") as f:
            self.assertIsNone(restricted_case_message(f.read()))
        self.assertIsNone(restricted_case_message(self.not_found))
