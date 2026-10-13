#!/usr/bin/env python


import fnmatch
import json
import os
import sys
import time
import unittest
from unittest import mock

from httpx import Request

from juriscraper.lib.exceptions import PacerLoginException
from juriscraper.lib.test_utils import MockResponse, warn_or_crash_slow_parser
from juriscraper.pacer.http import PacerSession, check_if_logged_in_page
from tests import TESTS_ROOT_EXAMPLES_PACER


class PacerNeedLoginTest(unittest.IsolatedAsyncioTestCase):
    """Test if different pages require a log in."""

    def parse_files(self, path_root, file_ext):
        paths = []
        for root, _, filenames in os.walk(path_root):
            for filename in fnmatch.filter(filenames, file_ext):
                paths.append(os.path.join(root, filename))
        paths.sort()
        path_max_len = max(len(path) for path in paths) + 2
        for i, path in enumerate(paths):
            t1 = time.time()
            sys.stdout.write(f"{i}. Doing {path.ljust(path_max_len)}")
            dirname, filename = os.path.split(path)
            filename_sans_ext = filename.split(".")[0]
            json_path = os.path.join(dirname, f"{filename_sans_ext}.json")

            with open(path, "rb") as f:
                content = f.read()

            result = check_if_logged_in_page(content)

            if not os.path.exists(json_path):
                with open(json_path, "w") as f:
                    print(f"Creating new file at {json_path}")
                    json.dump(result, f, indent=2, sort_keys=True)
                continue
            with open(json_path) as f:
                j = json.load(f)
                self.assertEqual(j, result)
            t2 = time.time()
            duration = t2 - t1
            warn_or_crash_slow_parser(duration, max_duration=0.5)

            sys.stdout.write("✓\n")

    def test_parsing_auth_samples(self):
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "authentication_samples"
        )
        self.parse_files(path_root, "*.html")

    @mock.patch(
        "juriscraper.pacer.http.httpx.AsyncClient.get",
        side_effect=lambda *args, **kwargs: MockResponse(
            200,
            b"",
            headers={"content-type": "text/html"},
            request=Request(method="GET", url="https://example.com"),
        ),
    )
    @mock.patch(
        "juriscraper.pacer.http.check_if_logged_in_page",
        side_effect=lambda x: False,
    )
    async def test_do_an_additional_get_request(
        self, mock_get, mock_check_if_logged_in
    ):
        """Test if we can do an additional GET request after check_if_logged_in
        returned False, check_if_logged_in_page should be called 2 times and
        raise a PacerLoginException afterwards.
        """
        session = PacerSession(username="", password="")
        with self.assertRaises(PacerLoginException):
            await session.get("https://example.com")

        self.assertEqual(mock_check_if_logged_in.call_count, 2)

    @mock.patch(
        "juriscraper.pacer.http.httpx.AsyncClient.post",
        side_effect=lambda *args, **kwargs: MockResponse(
            200,
            b"",
            headers={"content-type": "text/html"},
            request=Request(method="POST", url="https://example.com"),
        ),
    )
    @mock.patch(
        "juriscraper.pacer.http.check_if_logged_in_page",
        side_effect=lambda x: False,
    )
    async def test_avoid_an_additional_post_request(
        self, mock_get, mock_check_if_logged_in
    ):
        """Test if we can avoid an additional POST request after
        check_if_logged_in returned False, check_if_logged_in_page should be
        called 1 time and raise a PacerLoginException afterwards.
        """
        session = PacerSession(username="", password="")
        with self.assertRaises(PacerLoginException):
            await session.post("https://example.com")
        self.assertEqual(mock_check_if_logged_in.call_count, 1)

    @mock.patch("juriscraper.pacer.http.httpx.AsyncClient.get")
    @mock.patch(
        "juriscraper.pacer.http.check_if_logged_in_page",
        side_effect=lambda x: False,
    )
    @mock.patch(
        "juriscraper.pacer.http.is_pdf",
        side_effect=lambda x: True,
    )
    async def test_avoid_an_additional_get_request_pdf(
        self, mock_get, mock_check_if_logged_in, mock_is_pdf
    ):
        """Test if we can avoid an additional GET requests if a PDF binary is
        returned, check_if_logged_in_page shouldn't be called.
        """
        session = PacerSession(username="", password="")
        await session.get("https://example.com")
        self.assertEqual(mock_check_if_logged_in.call_count, 0)
