#!/usr/bin/env python

import unittest

from requests.utils import dict_from_cookiejar

from juriscraper.lib.exceptions import PacerLoginException
from juriscraper.pacer.http import AcmsSession, PacerSession
from tests.network import SKIP_IF_NO_PACER_LOGIN, get_pacer_session


class PacerAuthTest(unittest.TestCase):
    """Test the authentication methods"""

    @SKIP_IF_NO_PACER_LOGIN
    def test_logging_into_pacer(self):
        try:
            self.session = get_pacer_session()
            self.session.login()
            self.assertIsNotNone(self.session)
            self.assertIsNotNone(
                self.session.cookies.get(
                    "NextGenCSO", None, domain=".uscourts.gov", path="/"
                )
            )
        except PacerLoginException:
            self.fail("Could not log into PACER")

    def test_logging_in_bad_credentials(self):
        """Make sure if username/password is incorrect an exception is throw"""
        session = PacerSession(username="foofoo", password="barbarbar")
        with self.assertRaises(PacerLoginException):
            session.login()

    @SKIP_IF_NO_PACER_LOGIN
    def test_get_acms_token(self):
        try:
            session = get_pacer_session()
            session.login()
            next_gen_cso = dict_from_cookiejar(session.cookies)["NextGenCSO"]
            self.session = AcmsSession(next_gen_cso=next_gen_cso)
            self.assertIsNotNone(self.session)
            self.assertIsNotNone(self.session.auth_data.get("AuthToken", None))
        except PacerLoginException:
            self.fail("Could not retrieve ACMS credentials")
