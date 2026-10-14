import asyncio
import time
import unittest
from collections.abc import Callable, Coroutine, Mapping

import httpx
from typing_extensions import override

from juriscraper.state.RequestManager import (
    USER_AGENT,
    ExponentialBackoff,
    RateLimit,
    RequestHandler,
    RequestManager,
    RetryHandler,
    ScheduledRequest,
)


def _ok_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, text="ok")


def _make_manager(
    transport_handler: Callable[[httpx.Request], httpx.Response]
    | Callable[
        [httpx.Request], Coroutine[None, None, httpx.Response]
    ] = _ok_handler,
    *,
    headers: Mapping[str, str] | None = None,
    handlers: list[RequestHandler] | None = None,
    retry: RetryHandler | None = None,
) -> RequestManager:
    manager = RequestManager(headers=headers, handlers=handlers, retry=retry)
    # Swap the transport so requests still travel the full httpx build/send
    # path but resolve against an in-process handler.
    manager._transport = httpx.MockTransport(transport_handler)
    return manager


class RequestManagerCoreTest(unittest.IsolatedAsyncioTestCase):
    @override
    async def asyncSetUp(self) -> None:
        self.manager = _make_manager()

    @override
    async def asyncTearDown(self) -> None:
        await self.manager.aclose()

    async def test_default_user_agent(self) -> None:
        self.assertEqual(self.manager.headers.get("User-Agent"), USER_AGENT)

    async def test_user_agent_already_contains_juriscraper_left_alone(
        self,
    ) -> None:
        manager = _make_manager(
            headers={"User-Agent": "Custom Juriscraper Build/1.0"}
        )
        try:
            self.assertEqual(
                manager.headers.get("User-Agent"),
                "Custom Juriscraper Build/1.0",
            )
        finally:
            await manager.aclose()

    async def test_user_agent_missing_juriscraper_gets_appended(self) -> None:
        manager = _make_manager(headers={"User-Agent": "CustomAgent/1.0"})
        try:
            ua = manager.headers.get("User-Agent")
            self.assertIn("CustomAgent/1.0", ua)
            self.assertIn(USER_AGENT, ua)
        finally:
            await manager.aclose()

    async def test_cache_control_and_pragma_headers_set(self) -> None:
        self.assertEqual(
            self.manager.headers.get("Cache-Control"),
            "no-cache, max-age=0, must-revalidate",
        )
        self.assertEqual(self.manager.headers.get("Pragma"), "no-cache")

    async def test_request_leaves_no_background_tasks(self) -> None:
        self.assertFalse(self.manager._requests)
        response = await self.manager.get("https://example.com/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.manager._requests)
        self.assertFalse(self.manager._send_lock.locked())

    async def test_get_post_put_delete_round_trip(self) -> None:
        seen: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.method)
            return httpx.Response(200, text="ok")

        manager = _make_manager(handler)
        try:
            r1 = await manager.get("https://example.com/g")
            r2 = await manager.post("https://example.com/p")
            r3 = await manager.put("https://example.com/pu")
            r4 = await manager.delete("https://example.com/d")
            self.assertEqual(
                [r.status_code for r in (r1, r2, r3, r4)], [200] * 4
            )
            self.assertEqual(seen, ["GET", "POST", "PUT", "DELETE"])
        finally:
            await manager.aclose()

    async def test_close_finishes_cleanup_and_closes_client(self) -> None:
        await self.manager.get("https://example.com/")
        await self.manager.aclose()
        assert self.manager._close_task is not None
        self.assertTrue(self.manager._close_task.done())
        self.assertFalse(self.manager._requests)
        self.assertTrue(self.manager.is_closed)

    async def test_follow_redirects_propagated_per_request(self) -> None:
        captured: list[object] = []

        class CapturingHandler(RequestHandler):
            @override
            async def before_send(
                self, manager: RequestManager, request: ScheduledRequest
            ) -> None:
                captured.append(request.follow_redirects)

        manager = _make_manager(handlers=[CapturingHandler()])
        try:
            await manager.get("https://example.com/", follow_redirects=False)
            await manager.get("https://example.com/", follow_redirects=True)
            self.assertEqual(captured, [False, True])
        finally:
            await manager.aclose()


class HandlerOrderingTest(unittest.IsolatedAsyncioTestCase):
    async def test_before_queue_runs_before_before_send_runs_before_send(
        self,
    ) -> None:
        events: list[tuple[str, float]] = []
        send_called = asyncio.Event()

        def handler(request: httpx.Request) -> httpx.Response:
            events.append(("send", time.monotonic()))
            send_called.set()
            return httpx.Response(200, text="ok")

        class Recorder(RequestHandler):
            @override
            async def before_send(
                self, manager: RequestManager, request: ScheduledRequest
            ) -> None:
                events.append(("before_send_start", time.monotonic()))
                await asyncio.sleep(0.01)
                events.append(("before_send_done", time.monotonic()))

            @override
            async def listen(
                self, manager: RequestManager, request: ScheduledRequest
            ) -> None:
                events.append(("listen_start", time.monotonic()))
                _ = await request.response
                events.append(("listen_done", time.monotonic()))

        manager = _make_manager(handler, handlers=[Recorder()])
        try:
            await manager.get("https://example.com/")
        finally:
            await manager.aclose()

        keys = [e[0] for e in events]
        # before_send must finish before the request is dispatched.
        self.assertLess(keys.index("before_send_done"), keys.index("send"))
        # listen starts before send and stays awake until response resolves.
        self.assertLess(keys.index("listen_start"), keys.index("send"))
        self.assertLess(keys.index("send"), keys.index("listen_done"))

    async def test_multiple_handlers_all_invoked_per_request(self) -> None:
        counts = {"before_send": 0, "listen": 0}

        class Counter(RequestHandler):
            @override
            async def before_send(
                self, manager: RequestManager, request: ScheduledRequest
            ) -> None:
                counts["before_send"] += 1

            @override
            async def listen(
                self, manager: RequestManager, request: ScheduledRequest
            ) -> None:
                counts["listen"] += 1
                _ = await request.response

        manager = _make_manager(handlers=[Counter(), Counter(), Counter()])
        try:
            await manager.get("https://example.com/")
        finally:
            await manager.aclose()

        self.assertEqual(counts, {"before_send": 3, "listen": 3})


class RateLimitTest(unittest.IsolatedAsyncioTestCase):
    async def test_zero_rps_raises(self) -> None:
        with self.assertRaises(ValueError):
            RateLimit(rps=0.0)

    async def test_negative_rps_raises(self) -> None:
        with self.assertRaises(ValueError):
            RateLimit(rps=-1.0)

    async def test_spacing_enforced_between_sequential_requests(self) -> None:
        rate = RateLimit(rps=10.0)  # 0.1s spacing
        manager = _make_manager(handlers=[rate])
        try:
            await manager.get("https://example.com/")
            start = time.monotonic()
            await manager.get("https://example.com/")
            elapsed = time.monotonic() - start
            self.assertGreaterEqual(elapsed, 0.1)
        finally:
            await manager.aclose()

    async def test_concurrent_before_send_calls_are_serialized(self) -> None:
        # The lock around _last_request_time should serialize *reservations*
        # even when callers fire concurrently. Without the lock, all callers
        # would read the same _last_request_time and sleep the same short
        # amount in parallel, defeating the rate limit.
        spacing = 0.05
        rate = RateLimit(rps=1.0 / spacing)
        n = 5
        manager = _make_manager()
        self.addAsyncCleanup(manager.aclose)

        async def reserve() -> None:
            req = ScheduledRequest("GET", "https://x/")
            await rate.before_send(manager, req)

        start = time.monotonic()
        await asyncio.gather(*[reserve() for _ in range(n)])
        elapsed = time.monotonic() - start

        # First reservation sleeps ~0, then each subsequent reservation
        # sleeps an additional `spacing`, so total wall time ≈ (n-1) * spacing.
        # Allow 20% slack for scheduler jitter on the lower bound.
        self.assertGreaterEqual(elapsed, (n - 1) * spacing)


class RetryTest(unittest.IsolatedAsyncioTestCase):
    async def test_retries_until_success(self) -> None:
        attempts = {"n": 0}

        def handler(request: httpx.Request) -> httpx.Response:
            attempts["n"] += 1
            if attempts["n"] < 3:
                return httpx.Response(500, text="fail")
            return httpx.Response(200, text="ok")

        manager = _make_manager(
            handler, retry=ExponentialBackoff(max_retries=3)
        )
        try:
            response = await manager.get("https://example.com/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(attempts["n"], 3)
        finally:
            await manager.aclose()

    async def test_exhausting_retries_surfaces_last_exception(self) -> None:
        attempts = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            return httpx.Response(500, text="fail")

        manager = _make_manager(
            handler, retry=ExponentialBackoff(max_retries=3)
        )
        try:
            with self.assertRaises(httpx.HTTPStatusError):
                await manager.get("https://example.com/")
            # max_retries=2 means at least 3 attempts should have been made
            # (initial + 2 retries). Without retries actually firing this is 1.
            self.assertGreaterEqual(attempts, 3)
        finally:
            await manager.aclose()

    async def test_last_try_is_response(self) -> None:
        n = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal n
            n += 1
            if n == 2:
                return httpx.Response(200, text="ok")
            return httpx.Response(500, text="fail")

        response: httpx.Response | None = None

        class Recorder(RequestHandler):
            @override
            async def listen(
                self, manager: RequestManager, request: ScheduledRequest
            ) -> None:
                nonlocal response
                response = await request.response

        manager = _make_manager(
            handler,
            handlers=[Recorder()],
            retry=ExponentialBackoff(max_retries=3),
        )
        try:
            _ = await manager.get("https://example.com/")
            assert response is not None
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, "ok")
        finally:
            await manager.aclose()


if __name__ == "__main__":
    unittest.main()
