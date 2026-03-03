from typing import Optional

from juriscraper.state.texas.common import TexasCommonScraper
from juriscraper.state.texas.court_of_appeals import TexasCourtOfAppealsScraper
from juriscraper.state.texas.court_of_criminal_appeals import (
    TexasCourtOfCriminalAppealsScraper,
)
from juriscraper.state.texas.supreme_court import TexasSupremeCourtScraper
from tests import TESTS_ROOT_EXAMPLES_STATES
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
