import json
import unittest
from unittest import mock

import httpx

from juriscraper.lib.exceptions import PacerLoginException
from juriscraper.pacer import AcmsCaseSearch, PacerSession


class AcmsCaseSearchTest(unittest.IsolatedAsyncioTestCase):
    """Test looking an ACMS case up by docket number through the API."""

    CASES = [
        {
            "pcx_caseid": "481e75a0-8940-46d4-bb54-1135c0b4b34b",
            "pcx_casenumber": "26-7519",
            "pcx_name": "Collins v. Spotify USA, Inc.",
        }
    ]

    def setUp(self):
        self.session = PacerSession(username="user", password="pass")
        self.addAsyncCleanup(self.session.aclose)
        # A court jar in place means no SAML handshake is attempted.
        self.session.acms_cookies["ca9"] = httpx.Cookies()
        self.get = mock.patch.object(httpx.AsyncClient, "get").start()
        self.addCleanup(mock.patch.stopall)
        self.report = AcmsCaseSearch("ca9", pacer_session=self.session)

    def _respond(self, cases):
        """Make the GET stand-in answer `cases` as JSON."""

        async def get(url, **kwargs):
            return httpx.Response(
                200, json=cases, request=httpx.Request("GET", url)
            )

        self.get.side_effect = get

    async def test_requires_token_before_any_request(self):
        """Without a stored token the search fails like every API call."""
        with self.assertRaisesRegex(PacerLoginException, "get_index_content"):
            await self.report.query("26-7519")
        self.get.assert_not_awaited()

    async def test_data_is_the_first_match(self):
        """The first case the API lists is the one reported."""
        self.session.store_acms_token("ca9", {"Token": "token"})
        self._respond(self.CASES)

        await self.report.query("26-7519")

        self.assertEqual(self.report.data, self.CASES[0])

    async def test_no_match_gives_empty_data(self):
        """An empty answer means no case, not an error."""
        self.session.store_acms_token("ca9", {"Token": "token"})
        self._respond([])

        await self.report.query("99-9999")

        self.assertEqual(self.report.data, {})

    def test_parses_saved_json(self):
        """Data can be loaded from saved text, as other reports allow."""
        self.report._parse_text(json.dumps(self.CASES))

        self.assertEqual(self.report.data, self.CASES[0])

    async def test_requires_session(self):
        """A report without a session cannot query."""
        with self.assertRaises(AssertionError):
            await AcmsCaseSearch("ca9").query("26-7519")
