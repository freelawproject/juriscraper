"""Abstract base class for state-level docket enumeration scrapers.

This module provides a base class for scrapers that enumerate dockets across
multiple courts within a state. Unlike DocketSite which parses docket details,
BaseStateScraper is designed for discovering and listing dockets.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Callable
from datetime import date
from types import TracebackType
from typing import (
    ClassVar,
    Self,
    TypedDict,
    TypeVar,
    Unpack,
)

import httpx

from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.type_utils import (
    AsyncClientOptions,
    GetRequestOptions,
    PostRequestOptions,
)

logger = make_default_logger()

T = TypeVar("T")

# Type alias for response callback functions
# Callback receives the request manager and the response
ResponseCallback = Callable[["ScraperRequestManager", httpx.Response], None]


class ScraperRequestManager:
    """Manages HTTP requests for scrapers with callback support.

    This class encapsulates HTTP request handling with support for:
    - Session management with default Juriscraper headers
    - Response callbacks for logging/debugging

    Attributes:
        session: The httpx AsyncClient used for HTTP requests
        all_response_fn: Optional callback invoked after every HTTP response
    """

    def __init__(
        self,
        session: httpx.AsyncClient | None = None,
        all_response_fn: ResponseCallback | None = None,
        **kwargs: Unpack[AsyncClientOptions],
    ) -> None:
        """Initialize the request manager.

        Args:
            session: Optional httpx AsyncClient. If not provided, a new session
                will be created with default Juriscraper headers. Closing the
                manager also closes a supplied session.
            all_response_fn: Optional callback function invoked after every
                HTTP response (both request and archived_request). Receives
                the request manager instance and the response object.
        """
        if session is not None:
            if bool(kwargs):
                raise ValueError(
                    "Configure client options on the supplied session."
                )
            self.session = session
        else:
            kwargs.setdefault("http2", True)
            kwargs.setdefault("follow_redirects", True)
            kwargs.setdefault("timeout", 60)
            headers = httpx.Headers(kwargs.get("headers"))
            headers.setdefault("User-Agent", "Juriscraper")
            headers.setdefault(
                "Cache-Control", "no-cache, max-age=0, must-revalidate"
            )
            headers.setdefault("Pragma", "no-cache")
            kwargs["headers"] = headers
            self.session = httpx.AsyncClient(**kwargs)

        self.all_response_fn = all_response_fn

    async def aclose(self) -> None:
        """Close the HTTP session."""
        await self.session.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Unpack[PostRequestOptions],
    ) -> httpx.Response:
        """Make an HTTP request using the internal session.

        This method mirrors the httpx library's request method signature.
        The all_response_fn callback (if set) will be invoked after the
        request completes.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional arguments passed to session.request()
                (params, data, json, headers, timeout, etc.)

        Returns:
            The httpx Response object
        """
        response = await self.session.request(method, url, **kwargs)

        if self.all_response_fn is not None:
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
    async def get(
        self, url: str, **kwargs: Unpack[GetRequestOptions]
    ) -> httpx.Response:
        """Make a GET request. See request() for details."""
        return await self.request("GET", url, **kwargs)

    async def post(
        self, url: str, **kwargs: Unpack[PostRequestOptions]
    ) -> httpx.Response:
        """Make a POST request. See request() for details."""
        return await self.request("POST", url, **kwargs)


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
        request_manager: The ScraperRequestManager handling HTTP requests
    """

    # Override in subclasses to add custom headers to all requests
    ADDITIONAL_HEADERS: dict[str, str] | None = None
    COURT_IDS: ClassVar[list[str]] = []

    def __init__(
        self,
        request_manager: ScraperRequestManager | None = None,
        **kwargs: Unpack[AsyncClientOptions],
    ) -> None:
        """Initialize the scraper.

        Args:
            request_manager: Optional ScraperRequestManager instance. If not
                provided, a new one will be created with default settings.
                Supplied managers remain caller-managed.
            **kwargs: HTTPX client options for a newly created request manager.
        """
        super().__init__()

        self._owns_request_manager = request_manager is None
        if request_manager is not None:
            if bool(kwargs):
                raise ValueError(
                    "Configure client options on the supplied request manager."
                )
            self.request_manager = request_manager
        else:
            self.request_manager = ScraperRequestManager(**kwargs)

        # Merge additional headers if defined by subclass
        if self.ADDITIONAL_HEADERS is not None:
            self.request_manager.merge_headers(self.ADDITIONAL_HEADERS)

    async def aclose(self) -> None:
        """Close the request manager only if this scraper created it."""
        if self._owns_request_manager:
            await self.request_manager.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()

    @abstractmethod
    def backfill(
        self,
        courts: list[str],
        date_range: tuple[date, date],
    ) -> AsyncGenerator[HasCaseUrl, None]:
        """Backfill dockets for multiple courts over a date range.

        Subclasses must implement this method to enumerate historical dockets.

        Args:
            courts: List of court identifiers to scrape
            date_range: Tuple of (start_date, end_date) inclusive

        Yields:
            Dicts having a case_url field.
        """
        ...
