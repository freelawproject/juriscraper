#!/usr/bin/env python


import os

from typing_extensions import override

from juriscraper.pacer import DocketHistoryReport
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseDocketHistoryReportTest(PacerParseTestCase):
    """Tests for the docket history report."""

    @override
    def setUp(self) -> None:
        self.maxDiff = 200000

    def test_parsing_history_documents(self) -> None:
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "docket_history_reports"
        )
        self.parse_files(path_root, "*.html", DocketHistoryReport)
