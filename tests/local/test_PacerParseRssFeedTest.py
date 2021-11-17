#!/usr/bin/env python


import os

from juriscraper.pacer.rss_feeds import PacerRssFeed
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseRssFeedTest(PacerParseTestCase):
    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_rss_parsing(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_PACER, "rss_feeds")
        self.parse_files(path_root, "*.xml", PacerRssFeed)
