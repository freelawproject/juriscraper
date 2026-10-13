import unittest
from collections.abc import Mapping, Sequence
from unittest import mock

import httpx
from typing_extensions import override

from juriscraper.lib.exceptions import PacerLoginException
from juriscraper.pacer import CaseQuery, PacerSession
from juriscraper.pacer.http import _iter_cookies
from tests.network import get_pacer_session


class PacerSessionTest(unittest.IsolatedAsyncioTestCase):
    """Test the PacerSession wrapper class"""

    @override
    def setUp(self) -> None:
        self.session = get_pacer_session()
        self.addAsyncCleanup(self.session.aclose)

    def test_data_transformation(self) -> None:
        """Test our data transformation routine for building out PACER-compliant
        multi-part form data
        """
        data = {"case_id": 123, "case_type": "something"}
        expected = {"case_id": (None, "123"), "case_type": (None, "something")}
        output = self.session._prepare_multipart_form_data(data)
        self.assertEqual(output, expected)

    @mock.patch("juriscraper.pacer.http.httpx.AsyncClient.request")
    async def test_ignores_non_data_posts(
        self, mock_post: mock.AsyncMock
    ) -> None:
        """Test that POSTs without a data parameter just pass through as normal.

        :param mock_post: mocked Session.post method
        """
        data = {"name": ("filename", "junk")}

        await self.session.post(
            "https://free.law", files=data, auto_login=False
        )

        self.assertTrue(
            mock_post.called, "request.Session.post should be called"
        )
        assert mock_post.call_args is not None
        request_kwargs: Mapping[str, object] = mock_post.call_args.kwargs
        self.assertEqual(
            data,
            request_kwargs["files"],
            "the data should not be changed if using a files call",
        )

    @mock.patch("juriscraper.pacer.http.httpx.AsyncClient.request")
    async def test_transforms_data_on_post(
        self, mock_post: mock.AsyncMock
    ) -> None:
        """Test that POSTs using the data parameter get transformed into PACER's
        delightfully odd multi-part form data.

        :param mock_post: mocked Session.post method
        """
        data = {"name": "dave", "age": 33}
        expected = {"name": (None, "dave"), "age": (None, "33")}

        await self.session.post(
            "https://free.law", data=data, auto_login=False
        )

        self.assertTrue(
            mock_post.called, "request.Session.post should be called"
        )
        assert mock_post.call_args is not None
        request_kwargs: Mapping[str, object] = mock_post.call_args.kwargs
        self.assertNotIn(
            "data",
            mock_post.call_args.kwargs,
            "we should intercept data arguments",
        )
        self.assertEqual(
            expected,
            request_kwargs["files"],
            "we should transform and populate the files argument",
        )

    @mock.patch("juriscraper.pacer.http.httpx.AsyncClient.request")
    async def test_sets_default_timeout(
        self, mock_post: mock.AsyncMock
    ) -> None:
        await self.session.post("https://free.law", data={}, auto_login=False)

        self.assertTrue(
            mock_post.called, "request.Session.post should be called"
        )
        assert mock_post.call_args is not None
        request_kwargs: Mapping[str, object] = mock_post.call_args.kwargs
        self.assertIn(
            "timeout",
            mock_post.call_args.kwargs,
            "we should add a default timeout automatically",
        )
        self.assertEqual(
            300, request_kwargs["timeout"], "default should be 300"
        )

    def test_scraper_has_session_attribute(self) -> None:
        report = CaseQuery("cand", PacerSession())
        try:
            report.session  # noqa: B018
        except AttributeError:
            self.fail("Did not have session attribute on CaseQuery object.")


class PacerSessionAcmsTest(unittest.IsolatedAsyncioTestCase):
    """Test the ACMS SAML handshake in PacerSession."""

    ACMS_DOMAIN = "ca9-showdoc.azurewebsites.us"
    SAML_PARAMS = {"SAMLResponse": "assertion", "RelayState": "state"}

    @override
    def setUp(self) -> None:
        self.session = PacerSession(username="user", password="pass")
        self.addAsyncCleanup(self.session.aclose)
        # establish_acms_session() refuses to run without a PACER session.
        self.session.cookies.set(
            "NextGenCSO", "token", domain="pacer.uscourts.gov"
        )
        # Stand-ins for the handshake's two network steps: the hidden inputs
        # scraped from the docket sheet, and the Saml2/Acs POST.
        self.saml_params = mock.patch.object(
            self.session,
            "_get_saml_auth_request_parameters",
            return_value=self.SAML_PARAMS,
        ).start()
        self.acs_post = mock.patch.object(
            self.session, "_prepare_login_request"
        ).start()
        self.addCleanup(mock.patch.stopall)

    def _acs_sets_cookies(self, cookie_names: Sequence[str]) -> None:
        """Make the Saml2/Acs stand-in behave like ACMS: answer 200 whether or
        not the login worked, and leave `cookie_names` in the session jar,
        Secure like the real ones.
        """

        def post(
            url: str,
            data: object,
            headers: object,
            *args: object,
            **kwargs: object,
        ) -> httpx.Response:
            response = httpx.Response(
                200,
                request=httpx.Request("POST", url),
                headers=[
                    (
                        "Set-Cookie",
                        f"{name}=value; Domain={self.ACMS_DOMAIN}; Path=/; Secure",
                    )
                    for name in cookie_names
                ],
            )
            self.session.cookies.extract_cookies(response)
            return response

        self.acs_post.side_effect = post

    async def test_requires_saml_response(self) -> None:
        """An expired PACER session lands on PACER's login form, whose hidden
        inputs are not SAML parameters. The handshake must stop there.
        """
        self.saml_params.return_value = {
            "loginForm": "loginForm",
            "javax.faces.ViewState": "-1",
        }
        with self.assertRaisesRegex(PacerLoginException, "No SAMLResponse"):
            await self.session.establish_acms_session("ca9")
        self.acs_post.assert_not_called()
        self.assertNotIn("ca9", self.session.acms_cookies)

    async def test_rejected_login_is_not_a_session(self) -> None:
        """A rejected SAML login answers 200 and still sets Azure's affinity
        cookies, but never the ASP.NET auth cookie.
        """
        self._acs_sets_cookies(["ARRAffinity", "ARRAffinitySameSite"])
        with self.assertRaisesRegex(PacerLoginException, "rejected"):
            await self.session.establish_acms_session("ca9")
        self.assertNotIn("ca9", self.session.acms_cookies)
        # The affinity cookies must not linger in the PACER jar either.
        self.assertFalse(
            any(
                cookie.domain.lstrip(".") == self.ACMS_DOMAIN
                for cookie in _iter_cookies(self.session.cookies)
            )
        )

    async def test_successful_login_moves_cookies_to_court_jar(self) -> None:
        """A successful login sets the (possibly chunked) auth cookie. All ACMS
        cookies move to the court's jar, desecured.
        """
        cookie_names = [
            "ARRAffinity",
            ".AspNetCore.saml2",
            ".AspNetCore.saml2C1",
        ]
        self._acs_sets_cookies(cookie_names)
        await self.session.establish_acms_session("ca9")

        self.acs_post.assert_awaited_once()
        assert self.acs_post.call_args is not None
        request_args: tuple[object, ...] = self.acs_post.call_args.args
        request_kwargs: Mapping[str, object] = self.acs_post.call_args.kwargs
        self.assertEqual(
            request_args[0],
            f"https://{self.ACMS_DOMAIN}/Saml2/Acs",
        )
        self.assertEqual(request_kwargs["data"], self.SAML_PARAMS)

        jar = self.session.acms_cookies["ca9"]
        cookies = list(_iter_cookies(jar))
        self.assertEqual(sorted(c.name for c in cookies), sorted(cookie_names))
        self.assertFalse(
            any(c.secure for c in cookies), "ACMS cookies must be desecured"
        )
        self.assertFalse(
            any(
                cookie.domain.lstrip(".") == self.ACMS_DOMAIN
                for cookie in _iter_cookies(self.session.cookies)
            )
        )
