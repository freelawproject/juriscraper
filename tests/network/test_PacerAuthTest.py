#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function

import unittest

from juriscraper.lib.exceptions import PacerLoginException
from juriscraper.pacer.http import PacerSession
from tests.network import SKIP_IF_NO_PACER_LOGIN, get_pacer_session


class PacerAuthTest(unittest.TestCase):
    """Test the authentication methods"""

    @SKIP_IF_NO_PACER_LOGIN
    def test_logging_into_pacer(self):
        try:
            self.session = get_pacer_session()
            self.session.login()
            self.assertIsNotNone(self.session)
            self.assertIsNotNone(self.session.cookies.get(
                'PacerSession', None, domain='.uscourts.gov', path='/'))

        except PacerLoginException:
            self.fail('Could not log into PACER')

    def test_logging_in_bad_credentials(self):
        # Make sure password is more than eight characters.
        session = PacerSession(username='foofoo', password='barbarbar')
        with self.assertRaises(PacerLoginException):
            session.login()

    def test_logging_short_password(self):
        """If a short password is provided, do we throw an appropriate
        exception?
        """
        session = PacerSession(username='foo', password='bar')
        with self.assertRaises(PacerLoginException):
            session.login()

    def test_logging_short_username(self):
        """If a username shorter than six characters is provided, do we
        throw an appropriate exception?
        """
        session = PacerSession(username='foo', password='barbarbar')
        with self.assertRaises(PacerLoginException):
            session.login()
