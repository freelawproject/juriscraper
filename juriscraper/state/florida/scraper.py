import asyncio
import time
from collections.abc import (
    AsyncIterable,
    Callable,
    Iterable,
    Mapping,
    Sequence,
)
from dataclasses import dataclass
from http.cookiejar import CookieJar
from typing import Any, Literal, NotRequired, Self, TypedDict, override

import httpx
from httpx import Auth, Cookies, Request, Response


class UseClientDefault: ...


USE_CLIENT_DEFAULT = UseClientDefault()


class ManagedRequest:
    def __init__(
        self,
        request: Request,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
    ):
        self.httpx_request: Request = request
        self.follow_redirects: bool | UseClientDefault = follow_redirects


@dataclass(frozen=True)
class MiddlewareHandles:
    before: bool
    after: bool
    error: bool


class RequestHandler:
    handles: MiddlewareHandles = MiddlewareHandles(
        before=False, after=False, error=False
    )

    async def before(
        self, manager: "RequestManager", request: ManagedRequest
    ): ...

    async def after(
        self,
        manager: "RequestManager",
        request: ManagedRequest,
        response: Response,
    ): ...

    async def error(
        self,
        manager: "RequestManager",
        request: ManagedRequest,
        response: Response | None,
        error: Exception,
    ): ...


def middleware(cls: type) -> type:
    before = hasattr(cls, "before") and callable(cls.before)
    after = hasattr(cls, "after") and callable(cls.after)
    error = hasattr(cls, "error") and callable(cls.error)

    if not issubclass(cls, RequestHandler):
        cls.__bases__ = (RequestHandler,) + cls.__bases__

    cls.handles = MiddlewareHandles(before=before, after=after, error=error)

    return cls


@middleware
class RateLimit(RequestHandler):
    def __init__(self, rps: float = 10):
        self.rp_ns: float = 1e9 / rps
        self._next_time: float = time.monotonic_ns() - self.rp_ns

    @override
    async def before(self, manager: "RequestManager", request: ManagedRequest):
        t = time.monotonic_ns()
        if t < self._next_time:
            self._next_time += self.rp_ns
            await asyncio.sleep((self._next_time - t) / 1e9)

    @override
    async def after(
        self,
        manager: "RequestManager",
        request: ManagedRequest,
        response: Response,
    ):
        self._next_time = max(
            self._next_time, time.monotonic_ns() + self.rp_ns
        )


@middleware
class Retry(RequestHandler):
    def __init__(self, max_retries: int = 3):
        self.max_retries: int = max_retries
        self.tries: dict[int, int] = {}

    @override
    async def before(self, manager: "RequestManager", request: ManagedRequest):
        self.tries[hash(request)] = self.tries.get(hash(request), 0) + 1

    @override
    async def error(
        self,
        manager: "RequestManager",
        request: ManagedRequest,
        response: Response | None,
        error: Exception,
    ):
        if self.tries[hash(request)] < self.max_retries:
            _ = manager.send(request)

    @override
    async def after(
        self,
        manager: "RequestManager",
        request: ManagedRequest,
        response: Response,
    ):
        _ = self.tries.pop(hash(request), None)


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


@dataclass
class PartitionedHandlers:
    before: list[RequestHandler]
    after: list[RequestHandler]
    error: list[RequestHandler]


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
        self.client: httpx.AsyncClient = httpx.AsyncClient(
            auth=auth,
            params=params,
            headers={
                "User Agent": "Free Law Project",
                "Cache-Control": "no-cache, max-age=0, must-revalidate",
                "Pragma": "no-cache",
            },
            cookies=cookies,
            timeout=timeout,
            follow_redirects=follow_redirects,
            default_encoding=default_encoding,
        )
        self.client.headers.update(headers)
        self.handlers: PartitionedHandlers = PartitionedHandlers(
            before=[h for h in handlers if h.handles.before],
            after=[h for h in handlers if h.handles.after],
            error=[h for h in handlers if h.handles.error],
        )

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
    ) -> httpx.Response | None:
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

        request = ManagedRequest(
            self.client.build_request(method, url, **request_kwargs),
            follow_redirects=follow_redirects,
        )

        return await self.send(request)

    async def send(self, request: ManagedRequest) -> Response | None:
        _ = await asyncio.gather(
            *[h.before(self, request) for h in self.handlers.before]
        )

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
            _ = await asyncio.gather(
                *[
                    h.error(self, request, response, e)
                    for h in self.handlers.error
                ]
            )
        else:
            _ = await asyncio.gather(
                *[
                    h.after(self, request, response)
                    for h in self.handlers.after
                ]
            )

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


class FloridaScraper:
    def __init__(self):
        self.manager = RequestManager(handlers=[RateLimit(), Retry()])
