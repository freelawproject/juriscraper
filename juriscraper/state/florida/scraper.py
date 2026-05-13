import asyncio
import threading
import time
from collections.abc import (
    AsyncIterable,
    Callable,
    Iterable,
    Mapping,
    Sequence,
    Coroutine,
)
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from http.cookiejar import CookieJar
from tracemalloc import stop
from turtle import st
from typing import (
    Any,
    Generic,
    Literal,
    NotRequired,
    TypedDict,
    TypeVar,
    override,
)

import httpx
from httpx import Auth, Cookies, Request, Response


class UseClientDefault: ...


USE_CLIENT_DEFAULT = UseClientDefault()


T = TypeVar("T")


# https://stackoverflow.com/a/78911765
def run_coroutine_sync(
    coroutine: Coroutine[Any, Any, T], timeout: float = 30
) -> T:
    def run_in_new_loop():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coroutine)
        finally:
            new_loop.close()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)

    if threading.current_thread() is threading.main_thread():
        if not loop.is_running():
            return loop.run_until_complete(coroutine)
        else:
            with ThreadPoolExecutor() as pool:
                future = pool.submit(run_in_new_loop)
                return future.result(timeout=timeout)
    else:
        return asyncio.run_coroutine_threadsafe(coroutine, loop).result()


@dataclass
class AsyncAttribute(Generic[T]):
    _event: asyncio.Event = field(default_factory=asyncio.Event)
    _value: T | None = None

    async def get(self) -> T | None:
        _ = await self._event.wait()
        return self._value

    async def set(self, value: T) -> None:
        self._value = value
        self._event.set()

    def clear(self):
        self._value = None
        self._event.clear()


@dataclass
class ScheduledRequest:
    httpx_request: Request
    ready: asyncio.Event = field(default_factory=asyncio.Event)
    follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT
    response: AsyncAttribute[Response | None] = AsyncAttribute()
    error: AsyncAttribute[Exception | None] = AsyncAttribute()

    async def mark_ready(self):
        self.ready.set()

    def clear(self):
        self.ready.clear()
        self.response.clear()
        self.error.clear()

    @override
    def __hash__(self):
        return hash((self.httpx_request, self.follow_redirects))


class RequestHandler:
    async def listen(
        self, manager: "RequestManager", request: ScheduledRequest
    ) -> None: ...


HTTPMethod = Literal[
    "GET",
    "HEAD",
    "POST",
    "PUT",
    "DELETE",
    "CONNECT",
    "OPTIONS",
    "TRACE",
    "PATCH",
]

PrimitiveData = str | int | float | bool | None
QueryParamsType = (
    Mapping[str, PrimitiveData | Sequence[PrimitiveData]]
    | list[tuple[str, PrimitiveData]]
    | tuple[tuple[str, PrimitiveData], ...]
    | str
    | bytes
)
HeaderType = (
    Mapping[str, str]
    | Mapping[bytes, bytes]
    | Sequence[tuple[str, str]]
    | Sequence[tuple[bytes, bytes]]
)
CookieType = Cookies | CookieJar | dict[str, str] | list[tuple[str, str]]
AuthType = (
    tuple[str | bytes, str | bytes] | Callable[[Request], Request] | Auth
)
RequestContentType = str | bytes | Iterable[bytes] | AsyncIterable[bytes]


class RequestArguments(TypedDict):
    content: NotRequired[RequestContentType]
    data: NotRequired[Mapping[str, Any]]
    json: NotRequired[Any]
    params: NotRequired[QueryParamsType]
    headers: NotRequired[HeaderType]
    cookies: NotRequired[CookieType]
    timeout: NotRequired[float]


class RequestManager:
    """Configurable request manager."""

    def __init__(
        self,
        handlers: list[RequestHandler] | None = None,
        *,
        auth: AuthType | None = None,
        params: QueryParamsType | None = None,
        headers: HeaderType | None = None,
        cookies: CookieType | None = None,
        timeout: float = 30.0,
        follow_redirects: bool = True,
        default_encoding: str | Callable[[bytes], str] = "utf-8",
    ) -> None:
        if handlers is None:
            handlers = []
        self.stop: asyncio.Event = asyncio.Event()
        self.queue: asyncio.Queue[ScheduledRequest] = asyncio.Queue[
            ScheduledRequest
        ]()
        self.client: httpx.AsyncClient = httpx.AsyncClient(
            auth=auth,
            params=params,
            headers={
                "User-Agent": "Free Law Project",
                "Cache-Control": "no-cache, max-age=0, must-revalidate",
                "Pragma": "no-cache",
            },
            cookies=cookies,
            timeout=timeout,
            follow_redirects=follow_redirects,
            default_encoding=default_encoding,
        )
        self.client.headers.update(headers or {})
        self.handlers: list[RequestHandler] = handlers

        _ = asyncio.create_task(self.loop(self.queue))

    async def loop(self, queue: asyncio.Queue[ScheduledRequest]):
        while not self.stop.is_set():
            first = await (
                await anext(
                    asyncio.as_completed([self.stop.wait(), queue.get()])
                )
            )

            if not isinstance(first, ScheduledRequest):
                return
            request = first

            try:
                async with asyncio.timeout(60):
                    _ = await request.ready.wait()
                _ = await self.send(request)
            except TimeoutError:
                await self.enqueue_request(request)
            finally:
                queue.task_done()

    async def enqueue_request(
        self, request: ScheduledRequest, ready: bool = True
    ):
        request.clear()
        if ready:
            _ = await request.mark_ready()
        await self.queue.put(request)

    async def request(
        self,
        method: HTTPMethod,
        url: str,
        *,
        content: RequestContentType | None = None,
        data: Mapping[str, Any] | None = None,
        json: Any | None = None,
        params: QueryParamsType | None = None,
        headers: HeaderType | None = None,
        cookies: CookieType | None = None,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: float | UseClientDefault | None = USE_CLIENT_DEFAULT,
    ) -> httpx.Response:
        request_kwargs = RequestArguments()
        if content is not None:
            request_kwargs["content"] = content
        if data is not None:
            request_kwargs["data"] = data
        if json is not None:
            request_kwargs["json"] = json
        if params is not None:
            request_kwargs["params"] = params
        if headers is not None:
            request_kwargs["headers"] = headers
        if cookies is not None:
            request_kwargs["cookies"] = cookies
        if timeout is not None and not isinstance(timeout, UseClientDefault):
            request_kwargs["timeout"] = timeout

        request = ScheduledRequest(
            self.client.build_request(method, url, **request_kwargs),
            follow_redirects=follow_redirects,
        )

        await self.enqueue_request(request, ready=False)
        _ = await asyncio.gather(
            *(
                [h.listen(self, request) for h in self.handlers]
                + [request.mark_ready()]
            )
        )

        response = await request.response.get()
        error = await request.error.get()

        if error:
            raise error

        if response is None:
            raise RuntimeError("Response is None")

        return response

    async def send(self, request: ScheduledRequest) -> Response | None:
        response = None
        try:
            if isinstance(request.follow_redirects, UseClientDefault):
                response = await self.client.send(
                    request.httpx_request,
                )
            else:
                response = await self.client.send(
                    request.httpx_request,
                    follow_redirects=request.follow_redirects,
                )
            _ = response.raise_for_status()
        except Exception as e:
            await request.error.set(e)
            await request.response.set(None)
        else:
            await request.error.set(None)
            await request.response.set(response)

        return response

    async def get(
        self,
        url: str,
        *,
        content: RequestContentType | None = None,
        data: Mapping[str, Any] | None = None,
        json: Any | None = None,
        params: QueryParamsType | None = None,
        headers: HeaderType | None = None,
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
        params: QueryParamsType | None = None,
        headers: HeaderType | None = None,
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
        params: QueryParamsType | None = None,
        headers: HeaderType | None = None,
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
        params: QueryParamsType | None = None,
        headers: HeaderType | None = None,
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
        if hasattr(self, "stop"):
            self.stop.set()
        if hasattr(self, "client"):
            run_coroutine_sync(self.client.aclose())


class RateLimit(RequestHandler):
    def __init__(self, rps: float = 10):
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
            error = await request.error.get()
            if error is None:
                return
            remaining_tries -= 1
            await manager.enqueue_request(request)


class FloridaScraper:
    def __init__(self):
        self.manager: RequestManager = RequestManager(
            handlers=[RateLimit(), Retry()]
        )
