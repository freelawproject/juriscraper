import os

from juriscraper.pacer import ACMSDocketReport
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseAppellateDocketTest(PacerParseTestCase):
    """Can we parse the appellate dockets effectively?"""

    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_appellate_dockets(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_PACER, "dockets", "acms")
        self.parse_files(path_root, "*.acms_json", ACMSDocketReport)
