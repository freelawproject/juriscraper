#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function

import unittest

from juriscraper.pacer import ShowCaseDocApi
from tests.network import get_pacer_session


class PacerShowCaseDocApiTest(unittest.TestCase):
    def setUp(self):
        self.pacer_session = get_pacer_session()

    def test_bankruptcy_fails(self):
        """Does initializing the API fail on bankruptcy courts?"""
        with self.assertRaises(AssertionError):
            ShowCaseDocApi("caeb", pacer_session=self.pacer_session)
