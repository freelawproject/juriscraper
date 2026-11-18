"""Tests for the error context, logging and bot challenge helpers"""

import logging
import unittest
from unittest import mock

import httpx

from juriscraper.lib.exceptions import (
    InsanityException,
    NoDownloadUrlError,
    UnexpectedContentTypeError,
    attach_error_context,
)
from juriscraper.lib.log_tools import log_error, make_default_logger
from juriscraper.lib.utils import check_download_url
from juriscraper.opinions.united_states.state import nev

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
        with self.assertLogs(logger, level="ERROR") as logs:
            exc = UnexpectedContentTypeError(
                "bad", fingerprint=["test-unexpected-content-type"]
            )
        self.assertEqual(
            exc.sentry_fingerprint, ["test-unexpected-content-type"]
        )
        self.assertEqual(logs.records[0].levelno, logging.ERROR)
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


class SiteErrorContextTest(unittest.IsolatedAsyncioTestCase):
    async def test_parse_attaches_context(self):
        """Any exception escaping parse says which scraper and page failed"""
        site = nev.Site()
        site._download = mock.AsyncMock(side_effect=ValueError("broken"))
        with self.assertRaises(ValueError) as cm:
            await site.parse()
        self.assertEqual(cm.exception.court_id, site.court_id)
        self.assertEqual(cm.exception.url, site.url)
