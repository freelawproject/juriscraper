import os

from juriscraper.scotus import SCOTUSDocketReport, SCOTUSDocketReportHTML
from tests import TESTS_ROOT_EXAMPLES_SCOTUS
from tests.local.PacerParseTestCase import PacerParseTestCase


class ScotusParseDocketTest(PacerParseTestCase):
    """Can we parse the scotus dockets effectively?"""

    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_scotus_json_dockets(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_SCOTUS, "dockets", "json")
        self.parse_files(path_root, "*.scotus_json", SCOTUSDocketReport)

    def test_parsing_scotus_html_dockets(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_SCOTUS, "dockets", "html")
        self.parse_files(path_root, "*.html", SCOTUSDocketReportHTML)
