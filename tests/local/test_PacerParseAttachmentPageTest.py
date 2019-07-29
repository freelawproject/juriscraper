#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from juriscraper.pacer import AttachmentPage
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseAttachmentPageTest(PacerParseTestCase):
    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_attachment_pages(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_PACER, "attachment_pages")
        self.parse_files(path_root, '*.html', AttachmentPage)
