import os

from juriscraper.pacer import ClaimsActivity
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerClaimsActivityTest(PacerParseTestCase):
    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_claims_activity_pages(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_PACER, "claims_activity")
        self.parse_files(path_root, "*.html", ClaimsActivity)
