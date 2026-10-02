"""Tests for the request manager every state scraper makes its requests with.

Pacing and retrying live here rather than in each scraper, so that a court
that can't take a sweep at full speed, or that hangs now and then, is handled
the same way wherever it is scraped.
"""

import time
import unittest
from typing import Any
from unittest import mock

import requests
from typing_extensions import override

from juriscraper.state import BaseStateScraper as base_module
from juriscraper.state.BaseStateScraper import ScraperRequestManager

URL = "https://www.example.court/search"


class FakeResponse:
    """A response carrying only the status the manager looks at."""

    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code


class RecordingManager(ScraperRequestManager):
    """A manager whose requests are answered from a script.

    `_send` is the one place a request is really made, so replacing it leaves
    the pacing and retrying that wrap it in place.
    """

    def __init__(self, *answers: Any, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.answers = list(answers)
        self.sent: list[tuple[str, str]] = []

    @override
    def _send(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        self.sent.append((method, url))
        answer = self.answers.pop(0) if self.answers else FakeResponse()
        if isinstance(answer, Exception):
            raise answer
        return answer  # type: ignore[return-value]


class RetryTest(unittest.TestCase):
    """Making a request again when the court didn't really answer it."""

    def test_one_request_by_default(self) -> None:
        """A scraper that says nothing about retrying gets what it always
        got: one request, and whatever came back."""
        manager = RecordingManager(requests.Timeout("hung"))

        with self.assertRaises(requests.Timeout):
            manager.get(URL)

        self.assertEqual(len(manager.sent), 1)

    def test_a_timeout_is_tried_again(self) -> None:
        """A court that hangs on one request often answers the next."""
        manager = RecordingManager(
            requests.Timeout("hung"), FakeResponse(), max_attempts=3
        )

        with (
            mock.patch.object(base_module.time, "sleep") as slept,
            self.assertLogs(level="WARNING"),
        ):
            response = manager.get(URL)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(manager.sent), 2)
        slept.assert_called_once_with(manager.retry_wait_seconds)

    def test_a_server_error_is_tried_again(self) -> None:
        """A court being restarted answers 503 and serves the same request a
        moment later."""
        manager = RecordingManager(
            FakeResponse(503), FakeResponse(200), max_attempts=3
        )

        with (
            mock.patch.object(base_module.time, "sleep"),
            self.assertLogs(level="WARNING"),
        ):
            response = manager.get(URL)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(manager.sent), 2)

    def test_the_courts_own_answer_is_not_second_guessed(self) -> None:
        """A 404 is what the court has to say, so repeating the request only
        spends another one."""
        manager = RecordingManager(FakeResponse(404), max_attempts=3)

        response = manager.get(URL)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(manager.sent), 1)

    def test_a_court_that_never_answers_raises(self) -> None:
        """Three hangs in a row is the site being down, not a hiccup, and the
        caller hears about it rather than getting an empty page."""
        manager = RecordingManager(
            *[requests.Timeout("hung")] * 3, max_attempts=3
        )

        with (
            mock.patch.object(base_module.time, "sleep"),
            self.assertLogs(level="WARNING"),
            self.assertRaises(requests.Timeout),
        ):
            manager.get(URL)

        self.assertEqual(len(manager.sent), 3)

    def test_the_wait_grows_with_each_attempt(self) -> None:
        """A court that is struggling is given longer, not asked harder."""
        manager = RecordingManager(
            requests.ConnectionError("refused"),
            requests.ConnectionError("refused"),
            FakeResponse(),
            max_attempts=3,
            retry_wait_seconds=2.0,
        )

        with (
            mock.patch.object(base_module.time, "sleep") as slept,
            self.assertLogs(level="WARNING"),
        ):
            manager.get(URL)

        self.assertEqual(
            [call.args[0] for call in slept.call_args_list], [2.0, 4.0]
        )


class PacingTest(unittest.TestCase):
    """Leaving room between requests."""

    def test_requests_are_not_paced_by_default(self) -> None:
        """Nothing waits unless a scraper asks it to."""
        manager = RecordingManager()

        started = time.monotonic()
        for _ in range(3):
            manager.get(URL)

        self.assertLess(time.monotonic() - started, 0.05)

    def test_requests_are_spaced_out(self) -> None:
        """A sweep is a thousand requests to one court's website, so they
        arrive at the pace the scraper was told to keep rather than as fast
        as the court can answer."""
        manager = RecordingManager(min_request_interval=0.05)

        started = time.monotonic()
        for _ in range(3):
            manager.get(URL)
        elapsed = time.monotonic() - started

        # The first request goes at once; the other two wait their turn.
        self.assertGreaterEqual(elapsed, 0.1)
        self.assertEqual(len(manager.sent), 3)

    def test_the_interval_is_a_floor_not_a_toll(self) -> None:
        """A request made long after the last one doesn't wait: the interval
        is the gap between requests, not a charge on each."""
        manager = RecordingManager(min_request_interval=0.05)
        manager.get(URL)
        time.sleep(0.05)

        started = time.monotonic()
        manager.get(URL)

        self.assertLess(time.monotonic() - started, 0.05)


if __name__ == "__main__":
    unittest.main()
