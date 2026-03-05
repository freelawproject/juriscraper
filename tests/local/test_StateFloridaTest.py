from juriscraper.state.florida.parties import FloridaPartyListParser
from tests import TESTS_ROOT_EXAMPLES_STATES
from tests.local.PacerParseTestCase import PacerParseTestCase

FLORIDA_ROOT = TESTS_ROOT_EXAMPLES_STATES / "florida"


class TexasParseFloridaTest(PacerParseTestCase):
    """Test parsing of data common to all Texas dockets"""

    def setUp(self):
        self.maxDiff = 200000

    def test_parties(self):
        path_root = FLORIDA_ROOT / "parties"
        self.parse_files(path_root, "*.compare.json", FloridaPartyListParser)
