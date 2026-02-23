from typing import Optional
import unittest

from juriscraper.state.texas.common import TexasCommonScraper
from juriscraper.state.texas.court_of_appeals import TexasCourtOfAppealsScraper
from juriscraper.state.texas.court_of_criminal_appeals import (
    TexasCourtOfCriminalAppealsScraper,
)
from juriscraper.state.texas.email import (
    get_tames_case_from_email_body,
    get_tames_court_from_subject,
)
from juriscraper.state.texas.supreme_court import TexasSupremeCourtScraper
from tests import TESTS_ROOT_EXAMPLES_STATES, Path
from tests.local.PacerParseTestCase import PacerParseTestCase


class TexasParseCommonDataTest(PacerParseTestCase):
    """Test parsing of data common to all Texas dockets"""

    def setUp(self):
        self.maxDiff = 200000

    def test_common(self):
        path_root = TESTS_ROOT_EXAMPLES_STATES / "texas" / "common"
        self.parse_files(path_root, "*.html", TexasCommonScraper)

    def test_supreme(self):
        path_root = TESTS_ROOT_EXAMPLES_STATES / "texas" / "sc"
        self.parse_files(path_root, "*.html", TexasSupremeCourtScraper)

    def test_coca(self):
        path_root = TESTS_ROOT_EXAMPLES_STATES / "texas" / "coca"
        self.parse_files(
            path_root, "*.html", TexasCourtOfCriminalAppealsScraper
        )

    def test_coa(self):
        path_root = TESTS_ROOT_EXAMPLES_STATES / "texas" / "coa"
        self.parse_files(path_root, "*.html", TexasCourtOfAppealsScraper)

    def test_docket_number_validation(self):
        cases: dict[str, Optional[str]] = {
            "01-23-": None,
            "05-13-": None,
            "07-07-0MISC-CV": None,
            "07-07-0SHEP-CV": None,
            "100th DAY = 10": None,
            "14-95-01311-CR": None,
            "PD-912-91": None,
            "": None,
            "20-": None,
            "D-1234": "D-1234",
            "1234": "1234",
            "12-34": "12-34",
            "WR-97907": "WR-97907",
            "PD-991-90": "PD-991-90",
            "12-34-1234A-12": "12-34-1234A-12",
        }

        for dn, expected in cases.items():
            with self.subTest(f"Docket number {dn}"):
                self.assertEqual(
                    TexasCommonScraper._validate_docket_number(dn), expected
                )

class TamesEmailParsingTest(unittest.TestCase):
    """Tests for parsing TAMES notification emails."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        import email as email_mod

        email_path = (
            Path(__file__).parent
            / ".."
            / "examples"
            / "state"
            / "texas"
            / "email"
            / "notification_email.txt"
        )
        cls.msg = email_mod.message_from_string(email_path.read_text())

    def test_get_tames_court_from_subject(self) -> None:
        court_id = get_tames_court_from_subject(self.msg["Subject"])
        self.assertEqual(court_id, "texas_coa01")

    def test_get_tames_case_from_email_body(self) -> None:
        body = self.msg.get_payload(decode=True).decode("utf-8")
        result = get_tames_case_from_email_body(body)
        self.assertEqual(
            result,
            {
                "url": "https://search.txcourts.gov/Case.aspx?cn=01-24-00089-CV",
                "case_number": "01-24-00089-CV",
            },
        )
