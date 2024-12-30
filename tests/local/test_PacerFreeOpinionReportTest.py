import os

from juriscraper.pacer.free_documents import FreeOpinionReport
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase

TESTS_ROOT_EXAMPLES_PACER_FREE_OPINION_REPORT = os.path.join(
    TESTS_ROOT_EXAMPLES_PACER, "free_opinion_report"
)


class PacerFreeOpinionReportTest(PacerParseTestCase):
    def setUp(self):
        self.maxDiff = 200000

    def test_free_opinion_report(self):
        self.parse_files(
            TESTS_ROOT_EXAMPLES_PACER_FREE_OPINION_REPORT,
            "*.html",
            FreeOpinionReport,
        )
