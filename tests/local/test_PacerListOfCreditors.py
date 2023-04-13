import os

from juriscraper.pacer import ListOfCreditors
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerListOfCreditorsTest(PacerParseTestCase):
    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_claims_activity_pages(self):
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "list_of_creditors"
        )
        self.parse_files(path_root, "*.html", ListOfCreditors)
