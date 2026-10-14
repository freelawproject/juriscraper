#!/usr/bin/env python


import os

from typing_extensions import override

from juriscraper.pacer import CaseQuery
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseCaseQueryTest(PacerParseTestCase):
    """Tests for the CaseQuery report."""

    @override
    def setUp(self) -> None:
        self.maxDiff = 200000

    def test_parsing_case_query_results(self) -> None:
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_PACER, "case_queries")
        self.parse_files(path_root, "*.html", CaseQuery)
