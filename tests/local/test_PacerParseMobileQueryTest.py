#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from juriscraper.pacer import MobileQuery
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseMobileQueryTest(PacerParseTestCase):
    """Tests for the MobileQuery report."""

    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_case_query_results(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_PACER, "mobile_queries")
        self.parse_files(path_root, "*.html", MobileQuery)
