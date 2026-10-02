"""Abstract base class for state-level docket enumeration scrapers.

This module provides a base class for scrapers that enumerate dockets across
multiple courts within a state. Unlike DocketSite which parses docket details,
BaseStateScraper is designed for discovering and listing dockets.
"""

import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from datetime import date
from typing import (
    Any,
    TypedDict,
    TypeVar,
)

import requests

from juriscraper.lib.log_tools import make_default_logger

logger = make_default_logger()

T = TypeVar("T")

# Type alias for response callback functions
# Callback receives the request manager and the response
ResponseCallback = Callable[["ScraperRequestManager", requests.Response], None]

# Statuses worth trying again: a court that is briefly overloaded or being
# restarted answers with one of these and serves the same request a moment
# later. A 4xx is the court's answer and repeating it only wastes a request.
RETRY_STATUS_CODES = frozenset({500, 502, 503, 504})


class ScraperRequestManager:
    """Manages HTTP requests for scrapers with callback support.

    This class encapsulates HTTP request handling with support for:
    - Session management with default Juriscraper headers
    - Response callbacks for logging/debugging

    Attributes:
        session: The requests Session used for HTTP requests
        all_response_fn: Optional callback invoked after every HTTP response
        min_request_interval: Seconds to leave between requests
        max_attempts: How many times to make a request that fails in a way
            worth repeating
        retry_wait_seconds: Seconds to wait before the second attempt, waited
            again for each attempt after it
    """

    def __init__(
        self,
        session: requests.Session | None = None,
        all_response_fn: ResponseCallback | None = None,
        min_request_interval: float = 0.0,
        max_attempts: int = 1,
        retry_wait_seconds: float = 2.0,
    ) -> None:
        """Initialize the request manager.

        Pacing and retrying are both off by default, so a scraper that says
        nothing about them behaves as it always has. A scraper sweeping a
        court that can't take the traffic, or one that hangs now and then,
        asks for them here rather than writing its own.

        Args:
            session: Optional requests Session. If not provided, a new session
                will be created with default Juriscraper headers.
            all_response_fn: Optional callback function invoked after every
                HTTP response (both request and archived_request). Receives
                the request manager instance and the response object.
            min_request_interval: Seconds to leave between one request and the
                next, so a small court site isn't swept at full speed. 0 makes
                requests as fast as the court answers them.
            max_attempts: How many times to make a request that times out, is
                refused, or is answered with one of `RETRY_STATUS_CODES`. 1
                makes every request once.
            retry_wait_seconds: How long to wait before trying again, waited
                once more for each attempt after the first.
        """
        if session is not None:
            self.session = session
        else:
            self.session = requests.Session()
            self.session.headers.update(
                {
                    "User-Agent": "Juriscraper",
                    "Cache-Control": "no-cache, max-age=0, must-revalidate",
                    "Pragma": "no-cache",
                }
            )

        self.all_response_fn = all_response_fn
        self.min_request_interval = min_request_interval
        self.max_attempts = max_attempts
        self.retry_wait_seconds = retry_wait_seconds
        self._last_request_at = 0.0

    def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> requests.Response:
        """Make an HTTP request using the internal session.

        This method mirrors the requests library's request method signature.
        The all_response_fn callback (if set) will be invoked after the
        request completes.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional arguments passed to session.request()
                (params, data, json, headers, timeout, etc.)

        Returns:
            The requests Response object, which may still carry an error
            status: only the statuses worth repeating are retried, and only
            until the attempts run out.

        Raises:
            requests.Timeout: If the last attempt never answered.
            requests.ConnectionError: If the last attempt couldn't connect.
        """
        kwargs.setdefault("timeout", 60)

        for attempt in range(1, self.max_attempts):
            try:
                response = self._attempt(method, url, **kwargs)
            except (requests.Timeout, requests.ConnectionError):
                trouble = "didn't answer"
            else:
                if response.status_code not in RETRY_STATUS_CODES:
                    return response
                trouble = f"answered {response.status_code}"
            logger.warning(
                "%s %s %s on attempt %s of %s; trying again.",
                method,
                url,
                trouble,
                attempt,
                self.max_attempts,
            )
            time.sleep(self.retry_wait_seconds * attempt)

        return self._attempt(method, url, **kwargs)

    def _attempt(
        self, method: str, url: str, **kwargs: Any
    ) -> requests.Response:
        """Make one request, once it is this request's turn.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional arguments passed to session.request()

        Returns:
            The requests Response object
        """
        if self.min_request_interval:
            due = self._last_request_at + self.min_request_interval
            if (wait := due - time.monotonic()) > 0:
                time.sleep(wait)
        try:
            return self._send(method, url, **kwargs)
        finally:
            # From when the court was asked, so that a slow answer doesn't
            # also cost the interval.
            self._last_request_at = time.monotonic()

    def _send(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """Make one request of the court, with nothing around it.

        This is the one place a request is really made, so a test double
        replaces this rather than `request`, and what wraps it — the pacing
        and the retrying — stays in play.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional arguments passed to session.request()

        Returns:
            The requests Response object
        """
        response = self.session.request(method, url, **kwargs)

        if self.all_response_fn:
            self.all_response_fn(self, response)

        return response

    def merge_headers(self, headers: dict[str, str]) -> None:
        """Merge additional headers into the session headers.

        Args:
            headers: Dictionary of headers to merge. Existing headers with
                the same keys will be overwritten.
        """
        self.session.headers.update(headers)

    # Convenience methods that mirror requests library
    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Make a GET request. See request() for details."""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        """Make a POST request. See request() for details."""
        return self.request("POST", url, **kwargs)


class HasCaseUrl(TypedDict):
    case_url: str


class BaseStateScraper(ABC):
    """Abstract base class for state-level docket enumeration.

    This class provides a foundation for scrapers that need to enumerate
    dockets from a court website. It delegates HTTP requests to a
    ScraperRequestManager instance.

    Attributes:
        ADDITIONAL_HEADERS: Class constant for headers to merge into the
            request manager's session. Override in subclasses if needed.
        COURT_IDS: list of court ids handled by the scraper.
        BACKFILLS_HISTORY: whether `backfill` can reach a date range that has
            already passed.
        request_manager: The ScraperRequestManager handling HTTP requests
    """

    # Override in subclasses to add custom headers to all requests
    ADDITIONAL_HEADERS: dict[str, str] | None = None
    COURT_IDS: list[str] = []

    # Whether this court lets `backfill` reach into the past. Some publish
    # only what they have scheduled ahead, so their `backfill` enumerates the
    # cases that are live rather than the ones filed in a window, and asking
    # them for last month yields nothing. A caller scheduling backfills reads
    # this rather than discovering it from an empty result.
    BACKFILLS_HISTORY: bool = True

    def __init__(
        self,
        request_manager: ScraperRequestManager | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the scraper.

        Args:
            request_manager: Optional ScraperRequestManager instance. If not
                provided, a new one will be created with default settings.
            **kwargs: Additional keyword arguments for subclass customization.
        """
        super().__init__()

        if request_manager is not None:
            self.request_manager = request_manager
        else:
            self.request_manager = ScraperRequestManager()

        # Merge additional headers if defined by subclass
        if self.ADDITIONAL_HEADERS is not None:
            self.request_manager.merge_headers(self.ADDITIONAL_HEADERS)

    @abstractmethod
    def backfill(
        self,
        courts: list[str],
        date_range: tuple[date, date],
    ) -> Generator[HasCaseUrl, None, None]:
        """Backfill dockets for multiple courts over a date range.

        Subclasses must implement this method to enumerate historical dockets.

        Args:
            courts: List of court identifiers to scrape
            date_range: Tuple of (start_date, end_date) inclusive. A scraper
                whose `BACKFILLS_HISTORY` is false can only answer for a
                range reaching into the future.

        Yields:
            Dicts having a case_url field.
        """
        ...
