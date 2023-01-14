#!/usr/bin/env python

import os

from juriscraper.pacer import AppellateAttachmentPage
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseAppellateAttachmentPageTest(PacerParseTestCase):
    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_appellate_attachment_pages(self):
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "appellate_attachment_pages"
        )

        self.parse_files(path_root, "ca*.html", AppellateAttachmentPage)
