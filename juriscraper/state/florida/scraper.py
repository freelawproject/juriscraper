import asyncio
import time
from abc import ABC, abstractmethod
from collections.abc import (
    AsyncIterable,
    Iterable,
    Mapping,
    Sequence,
)
from dataclasses import dataclass, field
from http.cookiejar import CookieJar
from typing import (
    Any,
    override,
)

import httpx
from httpx import USE_CLIENT_DEFAULT, Auth, Cookies, Request, Response
from httpx._client import UseClientDefault

from juriscraper.lib.log_tools import make_default_logger

logger = make_default_logger(__name__)


@dataclass
class ScheduledRequest:
    """Wrapper around httpx.Request that keeps track of the `follow_redirects`
    parameter and response or errors.

    Attributes:
        httpx_request: The wrapped `httpx.Request` object.
        follow_redirects: Whether the request should follow redirects.
        response_future: Future that resolves to the response or error."""

    httpx_request: Request
    follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT
    response_future: asyncio.Future[Response] = field(
        default_factory=asyncio.Future[Response]
    )

    def reset(self) -> None:
        """Reset the request to its initial state.

        Used when queueing a request to ensure that the response is unset."""
        _ = self.response_future.cancel("Request reset.")
        self.response_future = asyncio.Future()

    async def response(self) -> Response:
        """Wait for the response to be set and return it."""
        return await self.response_future


class RequestHandler(ABC):
    """Base class for request handlers."""

    @abstractmethod
    async def listen(
        self, manager: "RequestManager", request: ScheduledRequest
    ) -> None: ...


PrimitiveData = str | int | float | bool | None
CookieType = Cookies | CookieJar | dict[str, str] | list[tuple[str, str]]
RequestContentType = str | bytes | Iterable[bytes] | AsyncIterable[bytes]


USER_AGENT: str = "Juriscraper (Free Law Project)"


class RequestManager:
    """Wrapper around httpx.AsyncClient allowing configurable request
    handlers for retries, rate-limiting, logging, and more.

    Attributes:
        client: The httpx AsyncClient
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
            default_encoding: Default encoding for responses if not specified by `Content-Type`
                header (httpx AsyncClient passthrough)
        """
        logger.info("Creating request manager.")
        if handlers is None:
            handlers = []
        self._queue: asyncio.Queue[ScheduledRequest] = asyncio.Queue[
            ScheduledRequest
        ]()
        headers = httpx.Headers(headers)
        if "User-Agent" not in headers:
            headers.update({"User-Agent": USER_AGENT})
        else:
            if "Juriscraper" not in headers.get("User-Agent", ""):
                headers.update(
                    {
                        "User-Agent": headers.get("User-Agent", "")
                        + f" {USER_AGENT}"
                    }
                )
        headers.update(
            {
                "Cache-Control": "no-cache, max-age=0, must-revalidate",
                "Pragma": "no-cache",
            }
        )
        self.client: httpx.AsyncClient = httpx.AsyncClient(
            auth=auth,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            follow_redirects=follow_redirects,
            default_encoding=default_encoding,
        )
        self.handlers: list[RequestHandler] = list(handlers)
        self._loop_future: asyncio.Task[None] | None = None

    async def _loop(self, queue: asyncio.Queue[ScheduledRequest]) -> None:
        """Pull requests from the queue and handle them.

        Args:
            queue: The queue to pull requests from. Should be `self._queue`"""
        while True:
            logger.info("Waiting for request.")
            request = await queue.get()
            logger.info(
                "Got request: %s. Sending.",
                request.httpx_request.url,
            )
            _ = await self.send(request)
            logger.info(
                "Request sent: %s. Marking task as done.",
                request.httpx_request.url,
            )
            queue.task_done()

    async def close(self) -> None:
        """Close the request manager and its underlying client."""
        if self._loop_future:
            _ = self._loop_future.cancel()
        await self.client.aclose()

    async def _ensure_loop(self) -> None:
        """Start the request loop if it's not already running."""
        if not self._loop_future or self._loop_future.done():
            logger.info("Request loop not running. Starting.")
            self._loop_future = asyncio.ensure_future(self._loop(self._queue))

    async def enqueue_request(self, request: ScheduledRequest) -> None:
        """Push a request onto the queue to be processed.

        Resets the request's state before queueing.

        Args:
            request: The request to schedule."""
        await self._ensure_loop()
        request.reset()
        await self._queue.put(request)

    async def request(
        self,
        method: str,
        url: str,
        *,
        content: RequestContentType | None = None,
        data: Mapping[str, Any] | None = None,
        json: Any | None = None,
        params: Mapping[str, PrimitiveData | Sequence[PrimitiveData]]
        | None = None,
        headers: Mapping[str, str] | None = None,
        cookies: CookieType | None = None,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: float | UseClientDefault | None = USE_CLIENT_DEFAULT,
    ) -> Response:
        """Send a request and set all handlers to listen to it.

        Parameters are passed directly to `httpx.AsyncClient.send`.

        Responses will not be returned until the `listen` method has exited on
        all handlers.

        Args:
            method: The HTTP method for this request
            url: The URL to send the request to
            content: The content to send with the request
            data: The data to send with the request
            json: The JSON data to send with the request
            params: The query parameters to send with the request
            headers: The headers to send with the request
            cookies: The cookies to send with the request
            follow_redirects: Whether to follow redirect responses
            timeout: Response timeout

        Return:
            The response to the dispatched request after handler interference."""
        logger.info("Requesting %s %s", method, url)
        request = ScheduledRequest(
            self.client.build_request(
                method,
                url,
                content=content,
                data=data,
                json=json,
                params=params,
                headers=headers,
                cookies=cookies,
                timeout=timeout,
            ),
            follow_redirects=follow_redirects,
        )

        handler_tasks = {
            asyncio.ensure_future(h.listen(self, request))
            for h in self.handlers
        }
        logger.info("Handlers listening: %s", request.httpx_request.url)
        await self.enqueue_request(request)
        logger.info("Request queued: %s", request.httpx_request.url)
        _ = await asyncio.gather(*handler_tasks)
        logger.info("Handlers finished. Waiting for response: %s", url)

        return await request.response()

    async def send(self, request: ScheduledRequest) -> Response | None:
        """Send a `ScheduledRequest` and set the response or error on it accordingly.

        Args:
            request: The request to send.

        Returns:
            The `httpx.Response` or `None` if an error occurred."""
        response = None
        logger.info("Sending request: %s", request.httpx_request.url)
        try:
            response = await self.client.send(
                request.httpx_request,
                follow_redirects=request.follow_redirects,
            )
            _ = response.raise_for_status()
        except Exception as e:
            logger.warning(
                "Request failed: %s (%s)", request.httpx_request.url, str(e)
            )
            request.response_future.set_exception(e)
        else:
            logger.info("Request succeeded: %s", request.httpx_request.url)
            request.response_future.set_result(response)

        return response

    async def get(
        self,
        url: str,
        *,
        content: RequestContentType | None = None,
        data: Mapping[str, Any] | None = None,
        json: Any | None = None,
        params: Mapping[str, PrimitiveData | Sequence[PrimitiveData]]
        | None = None,
        headers: Mapping[str, str] | None = None,
        cookies: CookieType | None = None,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: float | UseClientDefault | None = USE_CLIENT_DEFAULT,
    ) -> Response:
        """Send a GET request. Convenience wrapper around `request`."""
        return await self.request(
            "GET",
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

    async def post(
        self,
        url: str,
        *,
        content: RequestContentType | None = None,
        data: Mapping[str, Any] | None = None,
        json: Any | None = None,
        params: Mapping[str, PrimitiveData | Sequence[PrimitiveData]]
        | None = None,
        headers: Mapping[str, str] | None = None,
        cookies: CookieType | None = None,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: float | UseClientDefault | None = USE_CLIENT_DEFAULT,
    ) -> Response:
        """Send a POST request. Convenience wrapper around `request`."""
        return await self.request(
            "POST",
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

    async def put(
        self,
        url: str,
        *,
        content: RequestContentType | None = None,
        data: Mapping[str, Any] | None = None,
        json: Any | None = None,
        params: Mapping[str, PrimitiveData | Sequence[PrimitiveData]]
        | None = None,
        headers: Mapping[str, str] | None = None,
        cookies: CookieType | None = None,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: float | UseClientDefault | None = USE_CLIENT_DEFAULT,
    ) -> Response:
        """Send a PUT request. Convenience wrapper around `request`."""
        return await self.request(
            "PUT",
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

    async def delete(
        self,
        url: str,
        *,
        content: RequestContentType | None = None,
        data: Mapping[str, Any] | None = None,
        json: Any | None = None,
        params: Mapping[str, PrimitiveData | Sequence[PrimitiveData]]
        | None = None,
        headers: Mapping[str, str] | None = None,
        cookies: CookieType | None = None,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: float | UseClientDefault | None = USE_CLIENT_DEFAULT,
    ) -> Response:
        """Send a DELETE request. Convenience wrapper around `request`."""
        return await self.request(
            "DELETE",
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

    def __del__(self) -> None:
        """Clean up allocated resources. Cancels the request loop if it's running
        and closes the client if it's open."""
        if hasattr(self, "loop_future") and self._loop_future:
            _ = self._loop_future.cancel()
        client = getattr(self, "client", None)
        if client is None or client.is_closed:
            return
        # Best-effort async cleanup; callers should prefer `await close()`.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                asyncio.run(client.aclose())
            except Exception:
                pass
        else:
            _ = loop.create_task(client.aclose())


class RateLimit(RequestHandler):
    """Handler to enforce a rate limit on requests.

    Attributes:
        rp_ns: The maximum number of requests per nanosecond (lol). Used to simplify rate checks."""

    def __init__(self, rps: float = 2.0) -> None:
        """Initialize the rate limit handler.

        Args:
            rps: The maximum number of requests to send per second."""
        self.rp_ns: float = 1e9 / rps
        self._next_time: float = time.monotonic_ns() - self.rp_ns

    @override
    async def listen(
        self, manager: RequestManager, request: ScheduledRequest
    ) -> None: ...


@dataclass
class Retry(RequestHandler):
    """Handler to retry failed requests.

    Attributes:
        max_retries: The maximum number of times to retry a given request
            before admitting failure."""

    max_retries: int = 3

    @override
    async def listen(
        self, manager: RequestManager, request: ScheduledRequest
    ) -> None:
        """Listen for events on a request.

        Awaits the response in a try-except block and retries the request if
        the `except` block is triggered and the maximum number of retries hasn't
        been hit yet.

        Args:
            manager: The `RequestManager` that called this handler.
            request: The request to listen to."""
        remaining_tries = self.max_retries
        while remaining_tries > 0:
            try:
                _ = await request.response()
            except Exception:
                remaining_tries -= 1
                await manager.enqueue_request(request)
            else:
                return


class FloridaScraper:
    def __init__(self) -> None:
        self.manager: RequestManager = RequestManager(
            handlers=[RateLimit(), Retry()]
        )
