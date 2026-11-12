import base64
import json
import unittest
from unittest import mock

import httpx

from juriscraper.lib.exceptions import PacerLoginException, ParsingException
from juriscraper.lib.network_utils import (
    AcmsApiClient,
    extract_acms_view_model,
)
from juriscraper.pacer import PacerSession


class ExtractAcmsViewModelTest(unittest.TestCase):
    """Test pulling the showDocViewModel object out of an ACMS page."""

    def test_decodes_object_followed_by_more_script(self):
        """Nested braces and code after the object do not truncate it."""
        html = (
            "<script>window.showDocViewModel = "
            '{"a": {"b": [1, {"c": "}"}]}, "d": 2};\n'
            "window.other = {};</script>"
        )
        self.assertEqual(
            extract_acms_view_model(html),
            {"a": {"b": [1, {"c": "}"}]}, "d": 2},
        )

    def test_missing_marker_raises(self):
        """A page with no view model is a parsing failure."""
        with self.assertRaisesRegex(ParsingException, "No showDocViewModel"):
            extract_acms_view_model("<div>Nothing to see</div>")

    def test_malformed_object_raises(self):
        """A view model that is not valid JSON is a parsing failure."""
        with self.assertRaisesRegex(ParsingException, "Could not decode"):
            extract_acms_view_model("window.showDocViewModel = {oops;")

    def test_non_object_raises(self):
        """A view model that is not an object is a parsing failure."""
        with self.assertRaisesRegex(ParsingException, "not a JSON object"):
            extract_acms_view_model("window.showDocViewModel = [1, 2];")


class AcmsApiClientIndexContentTest(unittest.IsolatedAsyncioTestCase):
    """Test loading a case's IndexContent page and keeping its API token."""

    INDEX_CONTENT_URL = (
        "https://ca9-showdoc.azurewebsites.us/Home/IndexContent"
    )
    LOGIN_URL = "https://ca9-showdoc.azurewebsites.us/Auth/Login?ReturnUrl=%2F"
    CASE = {
        "caseId": "481e75a0-8940-46d4-bb54-1135c0b4b34b",
        "caseNumber": "26-7519",
    }

    def setUp(self):
        self.session = PacerSession(username="user", password="pass")
        self.addAsyncCleanup(self.session.aclose)
        # A court jar in place means no SAML handshake is attempted.
        self.session.acms_cookies["ca9"] = httpx.Cookies()
        self.get = mock.patch.object(httpx.AsyncClient, "get").start()
        self.addCleanup(mock.patch.stopall)
        self.client = AcmsApiClient(self.session, "ca9")

    @staticmethod
    def _token(claims: dict) -> str:
        """Build a JWT-shaped string carrying `claims`; it is never verified."""
        payload = base64.urlsafe_b64encode(json.dumps(claims).encode())
        return f"header.{payload.decode().rstrip('=')}.signature"

    @staticmethod
    def _page(view_model: dict) -> str:
        """Wrap `view_model` the way the HTMX fragment does."""
        return (
            "<div id='docket'></div>\n<script>\n"
            f"window.showDocViewModel = {json.dumps(view_model)};\n"
            "</script>"
        )

    def _respond(self, text, status=200, url=INDEX_CONTENT_URL, history=()):
        """Make the GET stand-in answer `text` as if fetched from `url`."""

        async def get(request_url, **kwargs):
            request = httpx.Request("GET", url, params=kwargs.get("params"))
            return httpx.Response(
                status, text=text, request=request, history=list(history)
            )

        self.get.side_effect = get

    async def test_returns_view_model_and_stores_token(self):
        """The view model comes back and the token plus user data are kept."""
        token = self._token({"showDocClaims": {"CSOId": 1234}})
        self._respond(
            self._page(
                {
                    "caseDetails": [self.CASE],
                    "authTokenResult": {"token": token},
                }
            )
        )

        view_model = await self.client.get_index_content("26-7519")

        self.assertEqual(view_model["caseDetails"], [self.CASE])
        self.assertEqual(self.session.acms_tokens["ca9"], {"Token": token})
        self.assertEqual(
            self.session.acms_user_data,
            {"CsoId": "1234", "ContactType": "PACER Only"},
        )
        self.get.assert_awaited_once()
        self.assertEqual(self.get.call_args[0][0], self.INDEX_CONTENT_URL)
        self.assertEqual(
            self.get.call_args[1]["params"], {"caseIdentifier": "26-7519"}
        )

    async def test_token_without_account_claim_leaves_user_data_empty(self):
        """A token with no account id is kept, but no user data is derived."""
        token = self._token({"exp": 1})
        self._respond(
            self._page(
                {
                    "caseDetails": [self.CASE],
                    "authTokenResult": {"token": token},
                }
            )
        )

        await self.client.get_index_content("26-7519")

        self.assertEqual(self.session.acms_tokens["ca9"], {"Token": token})
        self.assertEqual(self.session.acms_user_data, {})

    async def test_page_without_token_changes_no_auth_state(self):
        """A page with no token still returns its data and stores nothing."""
        self._respond(self._page({"caseDetails": []}))

        view_model = await self.client.get_index_content("99-9999")

        self.assertEqual(view_model, {"caseDetails": []})
        self.assertNotIn("ca9", self.session.acms_tokens)

    async def test_login_redirect_raises_and_drops_court_jar(self):
        """Landing on the login page means the ACMS session is gone."""
        redirect = httpx.Response(
            302, request=httpx.Request("GET", self.INDEX_CONTENT_URL)
        )
        self._respond(
            "<form id='loginForm'></form>",
            url=self.LOGIN_URL,
            history=[redirect],
        )

        with self.assertRaisesRegex(PacerLoginException, "login page"):
            await self.client.get_index_content("26-7519")
        self.assertNotIn("ca9", self.session.acms_cookies)

    async def test_page_without_view_model_raises(self):
        """An authenticated page with no view model is a parsing failure."""
        self._respond("<div>Nothing to see</div>")

        with self.assertRaises(ParsingException):
            await self.client.get_index_content("26-7519")

    async def test_http_error_propagates(self):
        """Server errors are left to the caller to retry."""
        self._respond("Service Unavailable", status=503)

        with self.assertRaises(httpx.HTTPStatusError):
            await self.client.get_index_content("26-7519")
