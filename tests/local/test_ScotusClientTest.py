#!/usr/bin/env python

import os
import unittest

from juriscraper.lib.test_utils import MockResponse
from juriscraper.dockets.united_states.federal_appellate.scotus import clients
from tests import TESTS_ROOT_EXAMPLES_SCOTUS


class YAMockResponse(MockResponse):
    """Mock a Request Response"""

    def __init__(
        self,
        status_code,
        content=None,
        headers=None,
        request=None,
        url=None,
        reason: bytes = None,
    ):
        self.status_code = status_code
        self._content = content
        self.headers = headers
        self.request = request
        self.encoding = "utf-8"
        self.reason = reason
        self.url = url


class ScotusClientTest(unittest.TestCase):
    """Test the download client shared by SCOTUS modules."""

    def setUp(self):

        with open(
            os.path.join(TESTS_ROOT_EXAMPLES_SCOTUS, "scotus_23-175.json"),
            "rb",
        ) as _json:
            self.valid_docket = _json.read()

        self.docket_response = YAMockResponse(
            status_code=200,
            content=self.valid_docket,
            headers={
                "content-length": str(len(self.valid_docket)),
                "content-type": "application/json",
                "last-modified": "Fri, 25 Aug 2023 18:01:01 GMT",
            },
        )

        with open(
            os.path.join(
                TESTS_ROOT_EXAMPLES_SCOTUS, "scotus_access_denied.html"
            ),
            "rb",
        ) as _json:
            self.access_denied = _json.read()

        self.access_denied_response = YAMockResponse(
            status_code=200,
            content=self.access_denied,
            url="https://www.supremecourt.gov/RSS/Cases/JSON/22A1059.json",
            headers={
                "content-length": str(len(self.access_denied)),
                "content-type": "text/html",
                "last-modified": "Fri, 25 Aug 2023 18:02:02 GMT",
            },
        )

        self.code304_response = YAMockResponse(
            status_code=304,
            content="",
            headers={
                "Content-Length": "0",
            },
        )
        with open(
            os.path.join(
                TESTS_ROOT_EXAMPLES_SCOTUS, "scotus_JSON_not_found.html"
            ),
            "rb",
        ) as _html:
            self.not_found_page = _html.read()

        self.not_found_response = YAMockResponse(
            status_code=200,
            content=self.not_found_page,
            headers={
                "content-length": str(len(self.not_found_page)),
                "content-type": "text/html",
                "last-modified": "Tue, 4 Jul 2023 18:01:01 GMT",
            },
        )
        # TODO: mock the ConnectionError
        # self.nre = clients.NameResolutionError
        # self.ce = clients.ConnectionError
        # self.ce.__context__ = self.nre
        # self.ce_response = YAMockResponse(
        #     status_code=504, content=None, reason="Gateway Time-out"
        # )
        # self.ce_response.url = "URL"
        # self.ade_response = clients.AccessDeniedError

    def test_not_found_regex(self):
        """Search example 'Not Found' page"""
        nfp_text = self.not_found_page.decode()
        valid_text = self.valid_docket.decode()
        self.assertTrue(clients.not_found_regex.search(nfp_text))
        self.assertFalse(clients.not_found_regex.search(valid_text))

    def test_not_found_test(self):
        """Test example 'Not Found' page text"""
        self.assertTrue(clients._not_found_test(self.not_found_response.text))
        are_false = (
            self.docket_response,
            self.code304_response,
            self.access_denied_response,
        )
        for r in are_false:
            with self.subTest(r=r):
                self.assertFalse(clients._not_found_test(r.text))

    def test_is_not_found_page(self):
        """Test example 'Not Found' page text in Response"""
        self.assertTrue(clients.is_not_found_page(self.not_found_response))
        are_false = (
            self.docket_response,
            self.code304_response,
            self.access_denied_response,
        )
        for r in are_false:
            with self.subTest(r=r):
                self.assertFalse(clients.is_not_found_page(r))

    def test_is_stale_content(self):
        """Handle content whose 'Last-Updated' header is earlier than
        the 'If-Updated-Since' header sent in the download request.
        """
        self.assertTrue(clients.is_stale_content(self.code304_response))
        are_false = (
            self.docket_response,
            self.not_found_response,
            self.access_denied_response,
        )
        for r in are_false:
            with self.subTest(r=r):
                self.assertFalse(clients.is_stale_content(r))

    def test_access_denied_test(self):
        """Test example 'Access Denied' page text"""
        self.assertTrue(
            clients._access_denied_test(self.access_denied_response.text)
        )
        are_false = (
            self.docket_response,
            self.code304_response,
            self.not_found_response,
        )
        for r in are_false:
            with self.subTest(r=r):
                self.assertFalse(clients._access_denied_test(r.text))

    def test_is_access_denied_page(self):
        """Test example 'Access Denied' page text in Response"""
        self.assertTrue(
            clients.is_access_denied_page(self.access_denied_response)
        )
        are_false = (
            self.docket_response,
            self.code304_response,
            self.not_found_response,
        )
        for r in are_false:
            with self.subTest(r=r):
                self.assertFalse(clients.is_access_denied_page(r))

    def test_is_docket(self):
        """Check for a docket JSON representation. Does not validate the JSON
        itself."""
        self.assertTrue(clients.is_docket(self.docket_response))
        are_false = (
            self.access_denied_response,
            self.code304_response,
            self.not_found_response,
        )
        for r in are_false:
            with self.subTest(r=r):
                self.assertFalse(clients.is_docket(r))

    def test_jitter(self):
        """A float between zero and the number passed."""
        test_value = 42
        test_result = clients.jitter(test_value)
        self.assertGreaterEqual(
            test_result,
            0,
        )
        self.assertLessEqual(test_result, test_value)
        self.assertIsInstance(test_result, float)

    def test_random_ua(self):
        """It's a string. A User-Agent string."""
        result = clients.random_ua()
        all_ua = [r["ua"] for r in clients.AGENTS]
        self.assertIsInstance(result, str)
        self.assertIn(result, all_ua)

    # TODO: mock the ConnectionError
    def test_response_handler_connection_error(self):
        """Handle exceptions from server-side measures."""
        pass
        # with self.assertRaises(clients.ConnectionError):
        #     clients.response_handler(self.ce_response)

    # TODO: mock an exception that is not explicitly handled
    def test_response_handler_uncaught_error(self):
        """Logging for uncaught exceptions."""
        pass
        # with self.assertRaises(RuntimeError):
        #     clients.response_handler(RuntimeError("uncaught"))

    def test_response_handler_access_denied_error(self):
        """Handle 'Access Denied' page response."""
        with self.assertRaises(clients.AccessDeniedError):
            clients.response_handler(self.access_denied_response)

    def test_response_handler_not_exceptions(self):
        """Pass through inoffensive responses."""
        self.assertTrue(clients.is_docket(self.docket_response))
        should_pass = (
            self.docket_response,
            self.code304_response,
            self.not_found_response,
        )
        for r in should_pass:
            with self.subTest(r=r):
                self.assertEqual(r, clients.response_handler(r))
