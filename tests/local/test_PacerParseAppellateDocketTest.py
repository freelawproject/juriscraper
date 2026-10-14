#!/usr/bin/env python


import os

from typing_extensions import override

from juriscraper.pacer import AppellateDocketReport
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase


class PacerParseAppellateDocketTest(PacerParseTestCase):
    """Can we parse the appellate dockets effectively?"""

    @override
    def setUp(self) -> None:
        self.maxDiff = 200000

    def test_parsing_appellate_dockets(self) -> None:
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "dockets", "appellate"
        )
        self.parse_files(path_root, "*.html", AppellateDocketReport)
        # PacerParseTestCase().parse_files(path_root, '*.html', AppellateDocketReport)

    def test_not_docket_dockets(self) -> None:
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "dockets", "not_appellate_dockets"
        )
        self.parse_files(path_root, "*.html", AppellateDocketReport)
        # PacerParseTestCase().parse_files(path_root, '*.html', AppellateDocketReport)
