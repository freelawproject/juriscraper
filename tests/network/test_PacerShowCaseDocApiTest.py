#!/usr/bin/env python


import unittest

from juriscraper.pacer import ShowCaseDocApi
from tests.network import (
    SKIP_IF_NO_PACER_LOGIN,
    get_pacer_session,
    pacer_credentials_are_defined,
)


class PacerShowCaseDocApiTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if pacer_credentials_are_defined():
            self.session = get_pacer_session()
            self.addAsyncCleanup(self.session.aclose)
            self.report = ShowCaseDocApi("dcd", self.session)

    @SKIP_IF_NO_PACER_LOGIN
    async def test_queries(self):
        """Can we do basic queries?"""
        tests = (
            # A regular document
            (
                {
                    "pacer_case_id": "191424",  # English v. Trump
                    "document_number": "25",
                    "attachment_number": "",
                },
                "04506336643",
            ),
            # An attachment
            (
                {
                    "pacer_case_id": "191424",
                    "document_number": "24",
                    "attachment_number": "1",
                },
                "04506336563",
            ),
        )
        for test, expected in tests:
            await self.report.query(**test)
            got = self.report.data
            self.assertEqual(
                got,
                expected,
            )
