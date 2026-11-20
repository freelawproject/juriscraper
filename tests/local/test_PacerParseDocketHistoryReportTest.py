#!/usr/bin/env python


from juriscraper.pacer import DocketHistoryReport
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseDocketHistoryReportTest(PacerParseTestCase):
    """Tests for the docket history report."""

    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_history_documents(self):
        path_root = TESTS_ROOT_EXAMPLES_PACER / "docket_history_reports"
        self.parse_files(path_root, "*.html", DocketHistoryReport)
