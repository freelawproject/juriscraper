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
