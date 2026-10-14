#!/usr/bin/env python


import os

from typing_extensions import override

from juriscraper.pacer import InternetArchive
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseInternetArchiveReportTest(PacerParseTestCase):
    """Tests for the IA XML docket parser"""

    @override
    def setUp(self) -> None:
        self.maxDiff = 200000

    def test_parsing_ia_xml_files(self) -> None:
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "dockets_internet_archive"
        )
        self.parse_files(path_root, "*.xml", InternetArchive)
