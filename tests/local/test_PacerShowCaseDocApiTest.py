#!/usr/bin/env python


import unittest

from typing_extensions import override

from juriscraper.pacer import ShowCaseDocApi
from tests.network import get_pacer_session


class PacerShowCaseDocApiTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.pacer_session = get_pacer_session()

    def test_bankruptcy_fails(self) -> None:
        """Does initializing the API fail on bankruptcy courts?"""
        with self.assertRaises(AssertionError):
            ShowCaseDocApi("caeb", pacer_session=self.pacer_session)
