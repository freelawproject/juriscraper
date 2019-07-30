import os

from juriscraper.pacer import ClaimsRegister
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerClaimsRegisterTest(PacerParseTestCase):

    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_claims_register_pages(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_PACER, 'claims_registers')
        self.parse_files(path_root, '*.html', ClaimsRegister)
