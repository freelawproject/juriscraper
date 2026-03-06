from juriscraper.state.florida.cases import (
    FloridaCaseInfoParser,
    FloridaCaseListParser,
)
from juriscraper.state.florida.courts import FloridaCourtsParser
from juriscraper.state.florida.docket_entries import (
    FloridaDocketEntryListParser,
)
from juriscraper.state.florida.documents import FloridaDocumentAccessParser
from juriscraper.state.florida.parties import FloridaPartyListParser
from tests import TESTS_ROOT_EXAMPLES_STATES
from tests.local.PacerParseTestCase import PacerParseTestCase

FLORIDA_ROOT = TESTS_ROOT_EXAMPLES_STATES / "florida"


class FloridaParseTest(PacerParseTestCase):
    """Test parsing of Florida court API data"""

    def setUp(self):
        self.maxDiff = 200000

    def test_parties(self):
        path_root = FLORIDA_ROOT / "parties"
        self.parse_files(path_root, "*.compare.json", FloridaPartyListParser)

    def test_courts(self):
        path_root = FLORIDA_ROOT / "courts"
        self.parse_files(path_root, "*.compare.json", FloridaCourtsParser)

    def test_cases(self):
        path_root = FLORIDA_ROOT / "cases"
        self.parse_files(path_root, "*.compare.json", FloridaCaseListParser)

    def test_case_info(self):
        path_root = FLORIDA_ROOT / "case_info"
        self.parse_files(path_root, "*.compare.json", FloridaCaseInfoParser)

    def test_docket_entries(self):
        path_root = FLORIDA_ROOT / "docket_entries"
        self.parse_files(
            path_root, "*.compare.json", FloridaDocketEntryListParser
        )

    def test_documents(self):
        path_root = FLORIDA_ROOT / "documents"
        self.parse_files(
            path_root, "*.compare.json", FloridaDocumentAccessParser
        )
