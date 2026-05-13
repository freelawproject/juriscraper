import asyncio
import time
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
    httpx_request: Request
    ready: asyncio.Event = field(default_factory=asyncio.Event)
    follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT
    response_future: asyncio.Future[Response] = field(
        default_factory=asyncio.Future[Response]
    )

    async def mark_ready(self):
        self.ready.set()

    def reset(self):
        self.ready.clear()
        _ = self.response_future.cancel("Request reset.")
        self.response_future = asyncio.Future()

    async def response(self):
        return await self.response_future

    @override
    def __hash__(self):
        return hash((self.httpx_request, self.follow_redirects))


class RequestHandler:
    async def listen(
        self, manager: "RequestManager", request: ScheduledRequest
    ) -> None: ...


PrimitiveData = str | int | float | bool | None
CookieType = Cookies | CookieJar | dict[str, str] | list[tuple[str, str]]
RequestContentType = str | bytes | Iterable[bytes] | AsyncIterable[bytes]


USER_AGENT: str = "Juriscraper (Free Law Project)"


class RequestManager:
    """Configurable request manager."""

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
        logger.info("Creating request manager.")
        if handlers is None:
            handlers = []
        self.queue: asyncio.Queue[ScheduledRequest] = asyncio.Queue[
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
        self.loop_future: asyncio.Task[None] | None = None

    async def loop(self, queue: asyncio.Queue[ScheduledRequest]):
        while True:
            try:
                logger.info("Waiting for request.")
                request = await asyncio.wait_for(queue.get(), 10.0)
            except TimeoutError:
                logger.info("Timed out waiting for request. Looping...")
                continue
            try:
                logger.info(
                    "Got request: %s. Waiting for ready state.",
                    request.httpx_request.url,
                )
                _ = await asyncio.wait_for(request.ready.wait(), 60)
                logger.info("Sending request: %s", request.httpx_request.url)
                _ = await self.send(request)
            except TimeoutError:
                logger.info(
                    "Timed out waiting for ready state. Moving request %s to back of queue.",
                    request.httpx_request.url,
                )
                await self.enqueue_request(request)
            finally:
                queue.task_done()

    async def close(self):
        if self.loop_future:
            _ = self.loop_future.cancel()
        await self.client.aclose()

    async def ensure_loop(self):
        if not self.loop_future or self.loop_future.done():
            logger.info("Request loop not running. Starting.")
            self.loop_future = asyncio.ensure_future(self.loop(self.queue))

    async def enqueue_request(
        self, request: ScheduledRequest, ready: bool = True
    ):
        await self.ensure_loop()
        request.reset()
        if ready:
            _ = await request.mark_ready()
        await self.queue.put(request)

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
    ) -> httpx.Response:
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

        await self.enqueue_request(request, ready=False)
        logger.info("Request queued: %s", request.httpx_request.url)
        handler_tasks = {
            asyncio.ensure_future(h.listen(self, request))
            for h in self.handlers
        }
        logger.info("Handlers finished: %s", request.httpx_request.url)
        _ = await request.mark_ready()
        logger.info("Request ready: %s", request.httpx_request.url)
        logger.info(
            "Waiting for handlers to finish: %s", request.httpx_request.url
        )
        _ = await asyncio.gather(*handler_tasks)
        logger.info("Handlers finished. Waiting for response: %s", url)

        return await request.response()

    async def send(self, request: ScheduledRequest) -> Response | None:
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
    ):
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
    ):
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
    ):
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
    ):
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

    def __del__(self):
        if hasattr(self, "loop_future") and self.loop_future:
            _ = self.loop_future.cancel()
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
    def __init__(self, rps: float = 2.0):
        self.rp_ns: float = 1e9 / rps
        self._next_time: float = time.monotonic_ns() - self.rp_ns

    @override
    async def listen(
        self, manager: RequestManager, request: ScheduledRequest
    ) -> None: ...


class Retry(RequestHandler):
    def __init__(self, max_retries: int = 3):
        self.max_retries: int = max_retries
        self.tries: dict[int, int] = {}

    @override
    async def listen(
        self, manager: RequestManager, request: ScheduledRequest
    ) -> None:
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
    def __init__(self):
        self.manager: RequestManager = RequestManager(
            handlers=[RateLimit(), Retry()]
        )
