import os

from juriscraper.scotus.scotus_email import SCOTUSEmail
from tests import TESTS_ROOT_EXAMPLES_SCOTUS
from tests.local.PacerParseTestCase import PacerParseTestCase


class ScotusParseEmailTest(PacerParseTestCase):
    """Test parsing of Scotus emails"""

    def setUp(self):
        self.maxDiff = 200000

    def test_emails(self):
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_SCOTUS, "dockets", "email"
        )
        self.parse_files(path_root, "*.eml", SCOTUSEmail)
