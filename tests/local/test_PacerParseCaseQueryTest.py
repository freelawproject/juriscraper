#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from juriscraper.pacer import CaseQuery

from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseCaseQueryTest(PacerParseTestCase):
    """Tests for the CaseQuery report."""

    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_case_query_results(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_PACER, 'case_queries')
        self.parse_files(path_root, '*.html', CaseQuery)
