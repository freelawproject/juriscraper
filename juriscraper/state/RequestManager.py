"""Classes and utilities for an async httpx-based request manager for scrapers."""

import asyncio
import time
from collections.abc import AsyncIterable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from http.cookiejar import CookieJar
from types import TracebackType
from typing import Any

import httpx
from httpx import (
    URL,
    USE_CLIENT_DEFAULT,
    AsyncClient,
    Auth,
    Cookies,
    HTTPStatusError,
    NetworkError,
    Request,
    Response,
    TimeoutException,
)
from httpx._client import UseClientDefault

from juriscraper.lib.log_tools import make_default_logger

logger = make_default_logger()

USER_AGENT: str = "Juriscraper (Free Law Project)"

PrimitiveData = str | int | float | bool | None
CookieType = Cookies | CookieJar | dict[str, str] | list[tuple[str, str]]
RequestContentType = str | bytes | Iterable[bytes] | AsyncIterable[bytes]


class ScheduledRequest(Request):
    """Wrapper around httpx.Request that keeps track of the `follow_redirects`
    parameter and response or errors.

    Attributes:
        follow_redirects: Whether the request should follow redirects.
        response: Awaitable future for response or exception."""

    def __init__(
        self,
        method: str,
        url: str,
        *,
        content: RequestContentType | None = None,
        data: Mapping[str, PrimitiveData] | None = None,
        json: Any | None = None,
        params: Mapping[str, PrimitiveData | Sequence[PrimitiveData]]
        | None = None,
        headers: Mapping[str, str] | None = None,
        cookies: CookieType | None = None,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: float | UseClientDefault | None = USE_CLIENT_DEFAULT,
    ) -> None:
        super().__init__(
            method=method,
            url=url,
            content=content,
            data=data,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            extensions={"timeout": timeout},
        )
        self.follow_redirects: bool | UseClientDefault = follow_redirects
        self.response: asyncio.Future[Response] = asyncio.Future()

    @classmethod
    def _from_httpx_request(
        cls,
        request: Request,
        *,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
    ) -> "ScheduledRequest":
        """Wrap a pre-built :class:`httpx.Request` as a :class:`ScheduledRequest`.

        Use this when the request has already been produced via
        :meth:`httpx.AsyncClient.build_request`, so client-level configuration
        (``base_url``, default headers/cookies/params, timeout) is preserved.
        """
        instance = cls.__new__(cls)
        instance.__dict__.update(request.__dict__)
        instance.follow_redirects = follow_redirects
        instance.response = asyncio.Future()
        return instance


class RequestHandler:
    """Base class for request handlers."""

    async def before_send(
        self, manager: "RequestManager", request: ScheduledRequest
    ) -> None:
        """The RequestManager awaits this method before sending the request.

        Args:
            manager: The request manager sending the request
            request: The request being sent"""
        return

    async def listen(
        self, manager: "RequestManager", request: ScheduledRequest
    ) -> None:
        """The RequestManager spawns this method in a Task to listen to the
        request concurrently.

        Args:
            manager: The request manager sending the request
            request: The request being sent"""
        return


class RequestManager(AsyncClient):
    """Wrapper around httpx.AsyncClient allowing configurable request
    handlers for retries, rate-limiting, logging, and more.

    Attributes:
        handlers: Handlers to run on every request"""

    def __init__(
        self,
        handlers: Sequence[RequestHandler] | None = None,
        *,
        auth: tuple[str | bytes, str | bytes] | Auth | None = None,
        params: Mapping[str, PrimitiveData | Sequence[PrimitiveData]]
        | None = None,
        headers: Mapping[str, str] | None = None,
        cookies: CookieType | None = None,
        timeout: float = 30.0,
        follow_redirects: bool = True,
        base_url: URL | str = "",
        default_encoding: str = "utf-8",
    ) -> None:
        """Initialize the request manager.

        Args:
            handlers: Handlers to run on every request
            auth: Authentication to use when sending requests (httpx AsyncClient passthrough)
            params: Query parameters (httpx AsyncClient passthrough)
            headers: Headers to include in every request (httpx AsyncClient passthrough). If
                there is no "User-Agent" header specified, it will be added with the
                value "Juriscraper (Free Law Project)". If a value is specified, it will be
                forced to contain the Juriscraper user agent string (case-sensitive).
            cookies: Cookies to include in every request (httpx AsyncClient passthrough)
            timeout: Timeout for every request (httpx AsyncClient passthrough)
            follow_redirects: Whether to follow redirects (httpx AsyncClient passthrough)
            base_url: Base URL for every request (httpx AsyncClient passthrough)
            default_encoding: Default encoding for responses if not specified by `Content-Type`
                header (httpx AsyncClient passthrough)
        """
        extra_headers = {
            "Cache-Control": "no-cache, max-age=0, must-revalidate",
            "Pragma": "no-cache",
        }
        logger.info("Creating request manager.")
        headers = httpx.Headers(headers)
        ua_header = headers.setdefault("User-Agent", USER_AGENT)
        if "Juriscraper" not in ua_header:
            extra_headers |= {"User-Agent": ua_header + f" {USER_AGENT}"}
        headers.update(extra_headers)
        super().__init__(
            auth=auth,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            follow_redirects=follow_redirects,
            base_url=base_url,
            default_encoding=default_encoding,
        )
        if handlers is None:
            handlers = []
        self._queue: asyncio.Queue[ScheduledRequest] = asyncio.Queue[
            ScheduledRequest
        ]()
        self.handlers: list[RequestHandler] = list(handlers)
        self._loop_task: asyncio.Task[None] | None = None

    async def _loop(self, queue: asyncio.Queue[ScheduledRequest]) -> None:
        """Pull requests from the queue and handles them.

        Args:
            queue: The queue to pull requests from. Should be `self._queue`"""
        while True:
            logger.info("Waiting for request.")
            request = await queue.get()
            logger.info(
                "Got request: %s. Waiting for before_send to complete.",
                request.url,
            )
            _ = await asyncio.gather(
                *[
                    handler.before_send(self, request)
                    for handler in self.handlers
                ]
            )
            logger.info(
                "Handlers finished. Sending request: %s",
                request.url,
            )
            _ = await self.send(request)
            logger.info(
                "Request sent: %s. Marking task as done.",
                request.url,
            )
            queue.task_done()

    async def aclose(self) -> None:
        """Close the request manager and its underlying client."""
        if self._loop_task:
            _ = self._loop_task.cancel()
        await super().aclose()

    async def _ensure_loop(self) -> None:
        """Start the request loop if it's not already running."""
        if not self._loop_task or self._loop_task.done():
            logger.info("Request loop not running. Starting.")
            self._loop_task = asyncio.create_task(self._loop(self._queue))

    async def enqueue_request(self, request: ScheduledRequest) -> None:
        """Push a request onto the queue to be processed.

        Resets the request's state and awaits the `before_queue` methods of any
        handlers before queueing.

        Args:
            request: The request to schedule."""
        await self._ensure_loop()
        if request.response.done():
            request.response = asyncio.Future()
        logger.info(
            "Queueing request: %s",
            request.url,
        )
        await self._queue.put(request)

    async def request(
        self,
        method: str,
        url: str,
        *,
        content: RequestContentType | None = None,
        data: Mapping[str, PrimitiveData] | None = None,
        json: Any | None = None,
        params: Mapping[str, PrimitiveData | Sequence[PrimitiveData]]
        | None = None,
        headers: Mapping[str, str] | None = None,
        cookies: CookieType | None = None,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: float | UseClientDefault | None = USE_CLIENT_DEFAULT,
        **kwargs: Any,
    ) -> Response:
        """Send a request and set all handlers to listen to it.

        Parameters are passed directly to `httpx.AsyncClient.send`.

        Requests will not be sent until the `before_queue` method has exited on
        all handlers, and Responses will not be returned until the `listen`
        method has exited on all handlers.

        Args:
            method: The HTTP method for this request
            url: The URL to send the request to
            content: The content to send with the request
            data: The form data to send with the request
            json: The JSON data to send with the request
            params: The query parameters to send with the request
            headers: The headers to send with the request
            cookies: The cookies to send with the request
            follow_redirects: Whether to follow redirect responses
            timeout: Response timeout

        Return:
            The response to the dispatched request after handler interference."""
        logger.info("Requesting %s %s", method, url)
        request = self.build_request(
            method,
            url,
            content=content,
            data=data,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            follow_redirects=follow_redirects,
            timeout=timeout,
        )

        listen_tasks = {
            asyncio.create_task(h.listen(self, request)) for h in self.handlers
        }
        logger.info("Handlers listening: %s", request.url)
        _ = await self.enqueue_request(request)

        logger.info(
            "Request %s queued. Waiting for listen handlers to finish.",
            request.url,
        )
        _ = await asyncio.gather(*listen_tasks)
        logger.info(
            "Request queued and handlers finished. Waiting for response: %s",
            request.url,
        )

        return await request.response

    async def send(
        self, request: ScheduledRequest, **kwargs: Any
    ) -> Response | None:
        """Send a `ScheduledRequest` and set the response or error on it accordingly.

        Args:
            request: The request to send.

        Returns:
            The `httpx.Response` or `None` if an error occurred."""
        response = None
        logger.info("Sending request: %s", request.url)
        try:
            response = await super().send(
                request,
                follow_redirects=request.follow_redirects,
            )
            _ = response.raise_for_status()
        except Exception as e:
            logger.warning("Request failed: %s (%s)", request.url, str(e))
            request.response.set_exception(e)
        else:
            logger.info("Request succeeded: %s", request.url)
            request.response.set_result(response)

        return response

    def build_request(
        self,
        *args: Any,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        **kwargs: Any,
    ) -> ScheduledRequest:
        """Build a `ScheduledRequest` from the arguments passed to `request`."""
        return ScheduledRequest._from_httpx_request(
            super().build_request(*args, **kwargs),
            follow_redirects=follow_redirects,
        )

    async def __aenter__(self) -> "RequestManager":
        """Allows the client to be used as an async context manager."""
        _ = await super().__aenter__()
        await self._ensure_loop()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        if self._loop_task:
            _ = self._loop_task.cancel()
        await super().__aexit__()


class RateLimit(RequestHandler):
    """Handler to enforce a rate limit on requests."""

    def __init__(self, rps: float = 2.0) -> None:
        """Initialize the rate limit handler.

        Parameters:
            rps: The maximum number of requests to allow per second."""
        if rps <= 0.0:
            raise ValueError(
                "Request/second ratelimit must be greater than 0.0"
            )
        self._last_request_time: float = 0.0
        self._request_spacing: float = 1.0 / rps

    async def before_send(
        self, manager: "RequestManager", request: ScheduledRequest
    ) -> None:
        """Ensure that requests aren't sent faster than the rate limit."""
        elapsed = time.time() - self._last_request_time
        sleep_time = max(0.0, self._request_spacing - elapsed)
        self._last_request_time = time.time() + sleep_time
        await asyncio.sleep(sleep_time)


@dataclass
class Retry(RequestHandler):
    """Handler to retry failed requests with exponential backoff.

    Attributes:
        max_retries: The maximum number of times to retry a given request
            before admitting failure.
        backoff: The initial sleep time between retries.
        backoff_growth: The factor by which to increase the sleep time between retries.
        retry_codes: The HTTP status codes to retry on."""

    max_retries: int = 3
    backoff: float = 0.0
    backoff_growth: float = 1.0
    retry_codes: set[int] = field(
        default_factory=lambda: {500, 502, 503, 504, 506, 507, 508}
    )

    async def listen(
        self, manager: RequestManager, request: ScheduledRequest
    ) -> None:
        """Awaits the response in a try-except block and re-queues the request if
        the `except` block is triggered by an HTTP error in `retry_codes` and the
        maximum number of retries hasn't been hit yet."""
        backoff = self.backoff
        remaining_tries = self.max_retries
        while remaining_tries > 0:
            try:
                _ = await request.response
            except Exception as e:
                match e:
                    case HTTPStatusError():
                        if e.response.status_code not in self.retry_codes:
                            logger.error(
                                "Received %s from %s\nResponse: %s",
                                e.response.status_code,
                                e.request.url,
                                e.response.text,
                            )
                            return
                    case TimeoutException():
                        logger.error("Read timeout from %s", e.request.url)
                    case NetworkError():
                        logger.error("Network error from %s", e.request.url)
                    case _:
                        logger.exception(
                            "Unexpected error while processing request %s",
                            request.url,
                        )
                        return
                remaining_tries -= 1
                await asyncio.sleep(backoff)
                backoff *= self.backoff_growth
                await manager.enqueue_request(request)
