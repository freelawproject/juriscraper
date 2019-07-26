#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function
import unittest
from juriscraper.pacer import ShowCaseDocApi
from tests.network import SKIP_IF_NO_PACER_LOGIN, get_pacer_session, pacer_credentials_are_defined


class PacerShowCaseDocApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if pacer_credentials_are_defined():
            cls.pacer_session = get_pacer_session()
            cls.report = ShowCaseDocApi('dcd', cls.pacer_session)

    @SKIP_IF_NO_PACER_LOGIN
    def test_queries(self):
        """Can we do basic queries?"""
        tests = (
            # A regular document
            ({
                'pacer_case_id': '191424',  # English v. Trump
                'document_number': '25',
                'attachment_number': '',
            }, '04506336643'),
            # An attachment
            ({
                'pacer_case_id': '191424',
                'document_number': '24',
                'attachment_number': '1',
            }, '04506336563'),
        )
        for test, expected in tests:
            self.report.query(**test)
            got = self.report.data
            self.assertEqual(
                got,
                expected,
            )

    @SKIP_IF_NO_PACER_LOGIN
    def test_bankruptcy_fails(self):
        """Does initializing the API fail on bankruptcy courts?"""
        with self.assertRaises(AssertionError):
            ShowCaseDocApi('caeb', pacer_session=self.pacer_session)
