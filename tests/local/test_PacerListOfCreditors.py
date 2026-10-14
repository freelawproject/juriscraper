import os

from typing_extensions import override

from juriscraper.pacer import ListOfCreditors
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerListOfCreditorsTest(PacerParseTestCase):
    @override
    def setUp(self) -> None:
        self.maxDiff = 200000

    def test_parsing_claims_activity_pages(self) -> None:
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "list_of_creditors"
        )
        self.parse_files(path_root, "*.html", ListOfCreditors)
