#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from juriscraper.pacer import AppellateDocketReport
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseAppellateDocketTest(PacerParseTestCase):
    """Can we parse the appellate dockets effectively?"""

    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_appellate_dockets(self):
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "dockets", "appellate"
        )
        self.parse_files(path_root, "*.html", AppellateDocketReport)
        # PacerParseTestCase().parse_files(path_root, '*.html', AppellateDocketReport)

    def test_not_docket_dockets(self):
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "dockets", "not_appellate_dockets"
        )
        self.parse_files(path_root, "*.html", AppellateDocketReport)
        # PacerParseTestCase().parse_files(path_root, '*.html', AppellateDocketReport)
