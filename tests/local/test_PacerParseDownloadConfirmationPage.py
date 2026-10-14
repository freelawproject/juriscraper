#!/usr/bin/env python


import os

from typing_extensions import override

from juriscraper.pacer import DownloadConfirmationPage
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseDownloadConfirmationPage(PacerParseTestCase):
    @override
    def setUp(self) -> None:
        self.maxDiff = 200000

    def test_parsing_attachment_pages(self) -> None:
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "confirmation_pages"
        )
        self.parse_files(path_root, "*.html", DownloadConfirmationPage)
