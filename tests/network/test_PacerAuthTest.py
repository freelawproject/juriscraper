#!/usr/bin/env python

import unittest

from juriscraper.lib.exceptions import PacerLoginException
from juriscraper.pacer.http import PacerSession
from tests.network import SKIP_IF_NO_PACER_LOGIN, get_pacer_session


class PacerAuthTest(unittest.IsolatedAsyncioTestCase):
    """Test the authentication methods"""

    @SKIP_IF_NO_PACER_LOGIN
    async def test_logging_into_pacer(self):
        try:
            self.session = get_pacer_session()
            await self.session.login()
            self.assertIsNotNone(self.session)
            self.assertIsNotNone(
                self.session.cookies.get(
                    "NextGenCSO", None, domain=".uscourts.gov", path="/"
                )
            )
        except PacerLoginException:
            self.fail("Could not log into PACER")

    async def test_logging_in_bad_credentials(self):
        """Make sure if username/password is incorrect an exception is throw"""
        session = PacerSession(username="foofoo", password="barbarbar")
        with self.assertRaises(PacerLoginException):
            await session.login()
