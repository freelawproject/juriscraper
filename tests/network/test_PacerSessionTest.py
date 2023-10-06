import unittest
from unittest import mock

from juriscraper.pacer.utils import make_doc1_url
from tests.network import (
    PACER_PASSWORD,
    PACER_USERNAME,
    SKIP_IF_NO_PACER_LOGIN,
    get_pacer_session,
)


class PacerSessionTest(unittest.IsolatedAsyncioTestCase):
    """Test the PacerSession wrapper class"""

    def setUp(self):
        self.session = get_pacer_session()

    @mock.patch("juriscraper.pacer.http.PacerSession.login")
    @SKIP_IF_NO_PACER_LOGIN
    async def test_auto_login(self, mock_login):
        """Do we automatically log in if needed?"""
        court_id = "ksd"
        pacer_doc_id = "07902639735"
        url = make_doc1_url(court_id, pacer_doc_id, True)
        pacer_case_id = "81531"
        # This triggers and auto-login because we aren't logged in yet.
        self.session.username = PACER_USERNAME
        self.session.password = PACER_PASSWORD
        _ = await self.session.get(
            url,
            params={
                "case_id": pacer_case_id,
                "got_receipt": "1",
            },
            follow_redirects=True,
        )
        self.assertTrue(
            mock_login.called, "PacerSession.login() should be called."
        )
