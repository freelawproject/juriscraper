# -*- coding: utf-8 -*-

import unittest
from juriscraper.lib.html_utils import get_html5_parsed_text
from lxml.html import HtmlElement


class CleanXMLTestCase(unittest.TestCase):
    def test_bad_docket_data(self):
        with open("tests/examples/pacer/other/bad_page.html", "rt") as rf:
            data = rf.read()
        parsed = get_html5_parsed_text(data)
        self.assertTrue(isinstance(parsed, HtmlElement))
