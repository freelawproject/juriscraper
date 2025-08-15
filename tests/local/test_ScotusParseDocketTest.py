import os

from juriscraper.pacer import SCOTUSDocketReport
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class ScotusParseDocketTest(PacerParseTestCase):
    """Can we parse the scotus dockets effectively?"""

    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_scotus_json_dockets(self):
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "dockets", "scotus", "json"
        )
        self.parse_files(path_root, "*.scotus_json", SCOTUSDocketReport)
