import os

from juriscraper.state.texas.texas_case_email import TexasCaseMail
from tests import TESTS_ROOT_EXAMPLES
from tests.local.PacerParseTestCase import PacerParseTestCase


class ScotusParseEmailTest(PacerParseTestCase):
    """Test parsing of Texas Case Mail notifications"""

    def setUp(self):
        self.maxDiff = None

    def test_emails(self):
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES,
            "state",
            "texas",
            "email",
        )
        print(self.parse_files(path_root, "*.eml", TexasCaseMail))
