#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from juriscraper.pacer import InternetArchive

from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseInternetArchiveReportTest(PacerParseTestCase):
    """Tests for the IA XML docket parser"""

    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_ia_xml_files(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_PACER, 'dockets_internet_archive')
        self.parse_files(path_root, '*.xml', InternetArchive,
                         initialize_with_court=False)
