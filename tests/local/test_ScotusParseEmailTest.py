from pathlib import Path

from juriscraper.scotus.scotus_email import (
    SCOTUSEmail,
    _SCOTUSConfirmationPageScraper,
)
from tests import TESTS_ROOT_EXAMPLES_SCOTUS
from tests.local.PacerParseTestCase import PacerParseTestCase


class ScotusParseEmailTest(PacerParseTestCase):
    """Test parsing of Scotus emails"""

    def setUp(self):
        self.maxDiff = 200000
        self.path_root = Path(TESTS_ROOT_EXAMPLES_SCOTUS) / "email"

    def test_emails(self):
        self.parse_files(self.path_root, "*.eml", SCOTUSEmail)

    def test_subscription(self):
        self.parse_files(
            self.path_root / "confirmation",
            "*.html",
            _SCOTUSConfirmationPageScraper,
        )
