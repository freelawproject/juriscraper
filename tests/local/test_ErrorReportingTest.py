"""Tests for the error context, logging and bot challenge helpers"""

import logging
import unittest
from unittest import mock
from urllib.parse import urlparse

import httpx

from juriscraper.lib.bot_challenge import (
    detect_bot_challenge,
    raise_if_bot_challenge,
)
from juriscraper.lib.exceptions import (
    BadContentError,
    BotChallengeError,
    InsanityException,
    NoDownloadUrlError,
    UnexpectedContentTypeError,
    attach_error_context,
)
from juriscraper.lib.log_tools import log_error, make_default_logger
from juriscraper.lib.utils import check_download_url
from juriscraper.opinions.united_states.state import nev

CLOUDFLARE_PAGE = (
    b"<html><head><title>Just a moment...</title></head>"
    b"<body>Checking your browser</body></html>"
)
RADWARE_PAGE = b"<html><head><title>Bot Manager Captcha</title></head></html>"
IMPERVA_PAGE = (
    b"<html><body>Request unsuccessful. Incapsula incident ID: 1</body></html>"
)
PLAIN_PAGE = (
    b"<html><head><title>Opinions</title></head><body>ok</body></html>"
)
COURT_ID = "juriscraper.opinions.united_states.state.test"


class ErrorContextTest(unittest.TestCase):
    def test_attach_error_context_keeps_existing_values(self):
        """The innermost raise site wins over an outer frame"""
        exc = InsanityException("boom")
        attach_error_context(exc, court_id=COURT_ID, url="https://a")
        attach_error_context(exc, court_id="outer", owner="court-site")

        self.assertEqual(exc.court_id, COURT_ID)
        self.assertEqual(exc.url, "https://a")
        self.assertEqual(exc.sentry_owner, "court-site")
        self.assertIsNone(exc.sentry_fingerprint)

    def test_attach_error_context_on_httpx_error(self):
        """Third-party exceptions take the attributes too"""
        request = httpx.Request("GET", "https://a")
        exc = httpx.HTTPStatusError(
            "403", request=request, response=httpx.Response(403)
        )
        attach_error_context(exc, court_id=COURT_ID, url="https://a")
        self.assertEqual(exc.court_id, COURT_ID)
        self.assertEqual(exc.url, "https://a")

    def test_auto_logging_exception_keeps_fingerprint(self):
        """The fingerprint is stored and the log stays at the class level"""
        logger = make_default_logger()
        with self.assertLogs(logger, level="WARNING") as logs:
            exc = UnexpectedContentTypeError(
                "bad", fingerprint=["test-unexpected-content-type"]
            )
        self.assertEqual(
            exc.sentry_fingerprint, ["test-unexpected-content-type"]
        )
        self.assertEqual(logs.records[0].levelno, logging.WARNING)
        self.assertEqual(
            logs.records[0].fingerprint, ["test-unexpected-content-type"]
        )

    def test_no_download_url_error_has_a_message(self):
        with self.assertRaises(NoDownloadUrlError) as cm:
            check_download_url("")
        self.assertIn("empty", str(cm.exception))


class LogErrorTest(unittest.TestCase):
    def setUp(self):
        self.logger = make_default_logger()

    def test_groups_by_court(self):
        with self.assertLogs(self.logger, level="ERROR") as logs:
            log_error(
                self.logger,
                "zero-results",
                "%s: nothing found",
                COURT_ID,
                court_id=COURT_ID,
                url="https://a",
            )
        record = logs.records[0]
        self.assertEqual(record.getMessage(), f"{COURT_ID}: nothing found")
        self.assertEqual(record.fingerprint, ["zero-results", COURT_ID])
        self.assertEqual(record.court_id, COURT_ID)
        self.assertEqual(record.url, "https://a")

    def test_record_points_at_the_caller(self):
        with self.assertLogs(self.logger, level="ERROR") as logs:
            log_error(self.logger, "zero-results", "x", group_by="shared")
        self.assertEqual(logs.records[0].module, "test_ErrorReportingTest")
        self.assertEqual(
            logs.records[0].funcName, "test_record_points_at_the_caller"
        )

    def test_shared_key_and_exc_info(self):
        with self.assertLogs(self.logger, level="ERROR") as logs:
            try:
                raise ValueError("inner")
            except ValueError:
                log_error(
                    self.logger,
                    "doctor-extension",
                    "failed",
                    group_by="shared",
                    exc_info=True,
                    detail="x",
                )
        record = logs.records[0]
        self.assertEqual(record.fingerprint, ["doctor-extension"])
        self.assertIsNotNone(record.exc_info)
        self.assertEqual(record.detail, "x")


class BotChallengeTest(unittest.IsolatedAsyncioTestCase):
    def test_detects_vendors(self):
        pages = [
            (CLOUDFLARE_PAGE, "cloudflare"),
            (RADWARE_PAGE, "radware"),
            (IMPERVA_PAGE, "imperva"),
            (PLAIN_PAGE, None),
            (CLOUDFLARE_PAGE.decode(), "cloudflare"),
        ]
        for body, vendor in pages:
            with self.subTest(vendor=vendor):
                self.assertEqual(detect_bot_challenge(body), vendor)

        headers = httpx.Headers({"cf-mitigated": "challenge"})
        self.assertEqual(
            detect_bot_challenge(PLAIN_PAGE, headers), "cloudflare"
        )

    def test_raise_if_bot_challenge_groups_by_host(self):
        url = "https://www.courts.example.gov/opinions?page=2"
        with self.assertRaises(BotChallengeError) as cm:
            raise_if_bot_challenge(CLOUDFLARE_PAGE, url, COURT_ID)
        exc = cm.exception
        self.assertEqual(
            exc.sentry_fingerprint, ["www.courts.example.gov", "bot-challenge"]
        )
        self.assertEqual(exc.sentry_owner, "court-site")
        self.assertEqual(exc.court_id, COURT_ID)
        self.assertEqual(exc.url, url)

        raise_if_bot_challenge(PLAIN_PAGE, url, COURT_ID)

    def _site_with_response(self, status: int, content: bytes) -> nev.Site:
        site = nev.Site()
        request = httpx.Request("GET", site.url)
        site.request["url"] = site.url
        site.request["response"] = httpx.Response(
            status, request=request, content=content
        )
        return site

    def test_post_process_response_raises_on_challenge(self):
        """A challenge page is reported as such, whatever the status code"""
        for status in (200, 403, 503):
            with self.subTest(status=status):
                site = self._site_with_response(status, CLOUDFLARE_PAGE)
                with self.assertRaises(BotChallengeError) as cm:
                    site._post_process_response()
                self.assertEqual(cm.exception.court_id, site.court_id)
                self.assertEqual(
                    cm.exception.sentry_fingerprint,
                    [urlparse(site.url).netloc, "bot-challenge"],
                )

    def test_post_process_response_keeps_http_errors(self):
        """A plain 403 still raises the httpx error"""
        site = self._site_with_response(403, PLAIN_PAGE)
        with self.assertRaises(httpx.HTTPStatusError):
            site._post_process_response()

    async def test_download_content_prefers_challenge_over_content_type(self):
        """A blocked PDF arrives as HTML; report the block, not the type"""
        site = nev.Site()
        site.expected_content_types = ["application/pdf"]
        url = "https://www.courts.example.gov/doc.pdf"
        response = httpx.Response(
            200,
            request=httpx.Request("GET", url),
            content=CLOUDFLARE_PAGE,
            headers={"Content-Type": "text/html"},
        )
        site.request["session"].get = mock.AsyncMock(return_value=response)

        with self.assertRaises(BotChallengeError) as cm:
            await site.download_content(url)
        self.assertEqual(cm.exception.url, url)
        self.assertNotIsInstance(cm.exception, UnexpectedContentTypeError)
        # callers that skip one bad document must still catch it
        self.assertIsInstance(cm.exception, BadContentError)

    async def test_parse_attaches_context(self):
        """Any exception escaping parse says which scraper and page failed"""
        site = nev.Site()
        site._download = mock.AsyncMock(side_effect=ValueError("broken"))
        with self.assertRaises(ValueError) as cm:
            await site.parse()
        self.assertEqual(cm.exception.court_id, site.court_id)
        self.assertEqual(cm.exception.url, site.url)
