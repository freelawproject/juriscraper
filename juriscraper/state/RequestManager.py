"""Classes and utilities for an async httpx-based request manager for scrapers."""

import asyncio
import time
from abc import ABC, abstractmethod
from collections.abc import (
    AsyncIterable,
    Awaitable,
    Iterable,
    Mapping,
    Sequence,
)
from contextvars import ContextVar
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
from typing_extensions import override

from juriscraper.lib.log_tools import make_default_logger

logger = make_default_logger()

USER_AGENT: str = "Juriscraper (Free Law Project)"

PrimitiveData = str | int | float | bool | None
CookieType = Cookies | CookieJar | dict[str, str] | list[tuple[str, str]]
RequestContentType = str | bytes | Iterable[bytes] | AsyncIterable[bytes]


async def _wait_for_cleanup(future: asyncio.Future[Any]) -> None:
    """Finish cleanup before propagating cancellation, including repeated cancels."""
    cancelled = None
    while not future.done():
        try:
            await asyncio.shield(future)
        except asyncio.CancelledError as exc:
            cancelled = exc
    future.result()
    if cancelled is not None:
        raise cancelled


async def _cancel_and_wait(futures: Iterable[asyncio.Future[Any]]) -> None:
    futures = tuple(futures)
    for future in futures:
        if not future.done():
            future.cancel()
    await _wait_for_cleanup(asyncio.gather(*futures, return_exceptions=True))


async def _run_tasks(*awaitables: Awaitable[Any]) -> None:
    futures = [asyncio.ensure_future(awaitable) for awaitable in awaitables]
    group = asyncio.gather(*futures)
    try:
        # Cancel children once, in cleanup, rather than through both gathers.
        await asyncio.shield(group)
    finally:
        try:
            await _cancel_and_wait(futures)
        finally:
            group.exception()


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
        self.attempt = 0

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
        instance.attempt = 0
        return instance


class RequestHandler:
    """Base class for request handlers.

    Handlers must not close their manager; its caller owns shutdown.
    """

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


class RetryHandler(ABC):
    @abstractmethod
    async def should_retry(
        self, request: ScheduledRequest, exc: Exception
    ) -> bool:
        """Whether or not a request should be retried based on the exception it raised. Once `True` is
        returned, the request will be scheduled again so handlers wishing to implement backoff
        logic should call `asyncio.sleep`.

        Args:
            request: The request instance
            exc: The exception raised by this request"""
        ...


class NoRetry(RetryHandler):
    @override
    async def should_retry(
        self, request: ScheduledRequest, exc: Exception
    ) -> bool:
        return False


@dataclass
class ExponentialBackoff(RetryHandler):
    """Retry handler with exponential backoff.

    Attributes:
        max_retries: The maximum number of times to retry a given request before
            admitting failure.
        backoff: The initial sleep time between retries.
        backoff_growth: The factor by which to increase the sleep time between
            retries.
        retry_codes: The HTTP status codes to retry on."""

    max_retries: int = 3
    backoff: float = 0.0
    backoff_growth: float = 1.0
    retry_codes: set[int] = field(
        default_factory=lambda: {500, 502, 503, 504, 506, 507, 508}
    )

    @override
    async def should_retry(
        self, request: ScheduledRequest, exc: Exception
    ) -> bool:
        if request.attempt > self.max_retries:
            return False

        match exc:
            case HTTPStatusError() as e if (
                e.response.status_code not in self.retry_codes
            ):
                return False
            case HTTPStatusError() | TimeoutException() | NetworkError() as e:
                logger.info(
                    "Attempt %s for %s (%r)", request.attempt, request.url, e
                )
                await asyncio.sleep(
                    self.backoff
                    * (self.backoff_growth ** (request.attempt - 1))
                )
                return True
            case _:
                return False


class RequestManager(AsyncClient):
    """Wrapper around httpx.AsyncClient allowing configurable request
    handlers for retries, rate-limiting, logging, and more.

    Attributes:
        handlers: Handlers to run on every request"""

    def __init__(
        self,
        handlers: Sequence[RequestHandler] | None = None,
        *,
        retry: RetryHandler | None = None,
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
            retry: Handler specifying when requests should be retried.
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
        if retry is None:
            retry = NoRetry()
        extra_headers = {
            "Cache-Control": "no-cache, max-age=0, must-revalidate",
            "Pragma": "no-cache",
        }
        logger.debug("Creating request manager.")
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
            http2=True,
            follow_redirects=follow_redirects,
            base_url=base_url,
            default_encoding=default_encoding,
        )
        if handlers is None:
            handlers = []
        self._retry_handler: RetryHandler = retry
        self.handlers: list[RequestHandler] = list(handlers)
        self._send_lock = asyncio.Lock()
        self._requests: dict[ScheduledRequest, asyncio.Task[Response]] = {}
        self._close_task: asyncio.Task[None] | None = None
        self._in_request: ContextVar[bool] = ContextVar(
            "request_manager_in_request", default=False
        )

    async def _send_request(self, request: ScheduledRequest) -> None:
        try:
            while not request.response.done():
                async with self._send_lock:
                    self._check_open()
                    if request.response.done():
                        break
                    await _run_tasks(
                        *(h.before_send(self, request) for h in self.handlers)
                    )
                    await self.send(request)
        except Exception as exc:
            if not request.response.done():
                request.response.set_exception(exc)
            raise

    def _check_open(self) -> None:
        if self._close_task is not None or self.is_closed:
            raise RuntimeError(
                "Cannot send a request, as the client is closed."
            )

    async def _close(self) -> None:
        try:
            await _cancel_and_wait(self._requests.values())
        finally:
            await super().aclose()

    @override
    async def aclose(self) -> None:
        """Close the request manager and its underlying client."""
        if self._in_request.get():
            raise RuntimeError("Request handlers cannot close their manager.")
        if self._close_task is None:
            self._close_task = asyncio.create_task(self._close())
        await _wait_for_cleanup(self._close_task)

    def _schedule_request(
        self, request: ScheduledRequest, *, listen: bool = False
    ) -> asyncio.Task[Response]:
        self._check_open()
        request.attempt += 1
        if request not in self._requests:
            task = asyncio.create_task(self._request(request, listen=listen))
            self._requests[request] = task

            def finished(task: asyncio.Task[Response]) -> None:
                self._requests.pop(request, None)
                request.response.cancel()
                if not request.response.cancelled():
                    request.response.exception()
                if not task.cancelled():
                    task.exception()

            task.add_done_callback(finished)
        return self._requests[request]

    async def enqueue_request(self, request: ScheduledRequest) -> None:
        """Schedule a request without waiting for its response.

        Increments the attempt count. An active request retries in its own task.

        Args:
            request: The request to schedule."""
        self._schedule_request(request)

    @override
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

        Requests will not be sent until the `before_send` method has exited on
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
            **kwargs: Arbitrary keyword arguments.

        Return:
            The response to the dispatched request after handler interference."""
        self._check_open()
        logger.debug("Requesting %s %s", method, url)
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

        task = self._schedule_request(request, listen=True)
        try:
            return await asyncio.shield(task)
        finally:
            await _cancel_and_wait((task,))

    async def _request(
        self, request: ScheduledRequest, *, listen: bool
    ) -> Response:
        async def wait_for_response() -> None:
            try:
                await request.response
            except Exception:
                # Raise request errors below, after listeners finish handling them.
                pass

        token = self._in_request.set(True)
        try:
            await _run_tasks(
                wait_for_response(),
                *(h.listen(self, request) for h in self.handlers if listen),
                self._send_request(request),
            )
            return request.response.result()
        finally:
            request.response.cancel()
            self._in_request.reset(token)

    @override
    async def send(
        self, request: ScheduledRequest, **kwargs: Any
    ) -> Response | None:
        """Send a `ScheduledRequest` and set the response or error on it accordingly.

        Args:
            request: The request to send.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The `httpx.Response` or `None` if an error occurred."""
        if request.response.cancelled():
            logger.warning("Request cancelled: %s", request.url)
            return None
        if request.response.done():
            logger.debug(
                "Request intercepted and response set (%s).", request.url
            )
            exc = request.response.exception()
            if exc:
                return None
            return request.response.result()
        self._check_open()
        response = None
        logger.debug("Sending request: %s", request.url)
        try:
            response = await super().send(
                request,
                follow_redirects=request.follow_redirects,
            )
            _ = response.raise_for_status()
        except Exception as e:
            if request.response.done():
                return response
            if await self._retry_handler.should_retry(request, e):
                if not request.response.done():
                    await self.enqueue_request(request)
                return None
            logger.warning("Request failed: %s (%s)", request.url, repr(e))
            if not request.response.done():
                request.response.set_exception(e)
        else:
            logger.debug("Request succeeded: %s", request.url)
            if not request.response.done():
                request.response.set_result(response)

        return response

    @override
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

    @override
    async def __aenter__(self) -> "RequestManager":
        """Allows the client to be used as an async context manager."""
        self._check_open()
        _ = await super().__aenter__()
        return self

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        await self.aclose()


class RateLimit(RequestHandler):
    """Handler to enforce a rate limit on requests."""

    def __init__(self, rps: float = 2.0) -> None:
        """Initialize the rate limit handler.

        Args:
            rps: The maximum number of requests to allow per second."""
        if rps <= 0.0:
            raise ValueError(
                "Request/second ratelimit must be greater than 0.0"
            )
        self._last_request_time: float = 0.0
        self._request_spacing: float = 1.0 / rps

    @override
    async def before_send(
        self, manager: "RequestManager", request: ScheduledRequest
    ) -> None:
        """Ensure that requests aren't sent faster than the rate limit."""
        elapsed = time.time() - self._last_request_time
        sleep_time = max(0.0, self._request_spacing - elapsed)
        self._last_request_time = time.time() + sleep_time
        await asyncio.sleep(sleep_time)
