from juriscraper.state.texas.common import TexasCommonScraper
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
