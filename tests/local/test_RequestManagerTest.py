import asyncio
import time
import unittest

import httpx

from juriscraper.state.RequestManager import (
    USER_AGENT,
    RateLimit,
    RequestHandler,
    RequestManager,
    Retry,
    ScheduledRequest,
)


def _ok_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, text="ok")


def _make_manager(transport_handler=_ok_handler, **kwargs) -> RequestManager:
    manager = RequestManager(**kwargs)
    # Swap the transport so requests still travel the full httpx build/send
    # path but resolve against an in-process handler.
    manager.client._transport = httpx.MockTransport(transport_handler)
    return manager


class RequestManagerCoreTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.manager = _make_manager()

    async def asyncTearDown(self):
        await self.manager.close()

    async def test_default_user_agent(self):
        self.assertEqual(
            self.manager.client.headers.get("User-Agent"), USER_AGENT
        )

    async def test_user_agent_already_contains_juriscraper_left_alone(self):
        manager = _make_manager(
            headers={"User-Agent": "Custom Juriscraper Build/1.0"}
        )
        try:
            self.assertEqual(
                manager.client.headers.get("User-Agent"),
                "Custom Juriscraper Build/1.0",
            )
        finally:
            await manager.close()

    async def test_user_agent_missing_juriscraper_gets_appended(self):
        manager = _make_manager(headers={"User-Agent": "CustomAgent/1.0"})
        try:
            ua = manager.client.headers.get("User-Agent")
            self.assertIn("CustomAgent/1.0", ua)
            self.assertIn(USER_AGENT, ua)
        finally:
            await manager.close()

    async def test_cache_control_and_pragma_headers_set(self):
        self.assertEqual(
            self.manager.client.headers.get("Cache-Control"),
            "no-cache, max-age=0, must-revalidate",
        )
        self.assertEqual(self.manager.client.headers.get("Pragma"), "no-cache")

    async def test_loop_started_lazily_on_first_enqueue(self):
        self.assertIsNone(self.manager._loop_future)
        response = await self.manager.get("https://example.com/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(self.manager._loop_future)

    async def test_get_post_put_delete_round_trip(self):
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
            await manager.close()

    async def test_close_cancels_loop_and_closes_client(self):
        await self.manager.get("https://example.com/")
        loop_future = self.manager._loop_future
        await self.manager.close()
        # Yield once so the cancellation can propagate.
        await asyncio.sleep(0)
        self.assertTrue(loop_future.cancelled() or loop_future.done())
        self.assertTrue(self.manager.client.is_closed)

    async def test_follow_redirects_propagated_per_request(self):
        captured: list[object] = []

        class CapturingHandler(RequestHandler):
            async def before_send(self, manager, request):
                captured.append(request.follow_redirects)

        manager = _make_manager(handlers=[CapturingHandler()])
        try:
            await manager.get("https://example.com/", follow_redirects=False)
            await manager.get("https://example.com/", follow_redirects=True)
            self.assertEqual(captured, [False, True])
        finally:
            await manager.close()


class HandlerOrderingTest(unittest.IsolatedAsyncioTestCase):
    async def test_before_queue_runs_before_before_send_runs_before_send(self):
        events: list[tuple[str, float]] = []
        send_called = asyncio.Event()

        def handler(request: httpx.Request) -> httpx.Response:
            events.append(("send", time.monotonic()))
            send_called.set()
            return httpx.Response(200, text="ok")

        class Recorder(RequestHandler):
            async def before_send(self, manager, request):
                events.append(("before_send_start", time.monotonic()))
                await asyncio.sleep(0.01)
                events.append(("before_send_done", time.monotonic()))

            async def listen(self, manager, request):
                events.append(("listen_start", time.monotonic()))
                _ = await request.response()
                events.append(("listen_done", time.monotonic()))

        manager = _make_manager(handler, handlers=[Recorder()])
        try:
            await manager.get("https://example.com/")
        finally:
            await manager.close()

        keys = [e[0] for e in events]
        # before_send must finish before the request is dispatched.
        self.assertLess(keys.index("before_send_done"), keys.index("send"))
        # listen starts before send and stays awake until response resolves.
        self.assertLess(keys.index("listen_start"), keys.index("send"))
        self.assertLess(keys.index("send"), keys.index("listen_done"))

    async def test_multiple_handlers_all_invoked_per_request(self):
        counts = {"before_send": 0, "listen": 0}

        class Counter(RequestHandler):
            async def before_send(self, manager, request):
                counts["before_send"] += 1

            async def listen(self, manager, request):
                counts["listen"] += 1
                _ = await request.response()

        manager = _make_manager(handlers=[Counter(), Counter(), Counter()])
        try:
            await manager.get("https://example.com/")
        finally:
            await manager.close()

        self.assertEqual(counts, {"before_send": 3, "listen": 3})


class RateLimitTest(unittest.IsolatedAsyncioTestCase):
    async def test_zero_rps_raises(self):
        with self.assertRaises(ValueError):
            RateLimit(rps=0.0)

    async def test_negative_rps_raises(self):
        with self.assertRaises(ValueError):
            RateLimit(rps=-1.0)

    async def test_spacing_enforced_between_sequential_requests(self):
        rate = RateLimit(rps=10.0)  # 0.1s spacing
        manager = _make_manager(handlers=[rate])
        try:
            await manager.get("https://example.com/")
            start = time.monotonic()
            await manager.get("https://example.com/")
            elapsed = time.monotonic() - start
            self.assertGreaterEqual(elapsed, 0.1)
        finally:
            await manager.close()

    async def test_concurrent_before_send_calls_are_serialized(self):
        # The lock around _last_request_time should serialize *reservations*
        # even when callers fire concurrently. Without the lock, all callers
        # would read the same _last_request_time and sleep the same short
        # amount in parallel, defeating the rate limit.
        spacing = 0.05
        rate = RateLimit(rps=1.0 / spacing)
        n = 5

        async def reserve():
            req = ScheduledRequest(httpx.Request("GET", "https://x/"))
            await rate.before_send(None, req)

        start = time.monotonic()
        await asyncio.gather(*[reserve() for _ in range(n)])
        elapsed = time.monotonic() - start

        # First reservation sleeps ~0, then each subsequent reservation
        # sleeps an additional `spacing`, so total wall time ≈ (n-1) * spacing.
        # Allow 20% slack for scheduler jitter on the lower bound.
        self.assertGreaterEqual(elapsed, (n - 1) * spacing)


class RetryTest(unittest.IsolatedAsyncioTestCase):
    async def test_retries_until_success(self):
        attempts = {"n": 0}

        def handler(request: httpx.Request) -> httpx.Response:
            attempts["n"] += 1
            if attempts["n"] < 3:
                return httpx.Response(500, text="fail")
            return httpx.Response(200, text="ok")

        manager = _make_manager(handler, handlers=[Retry(max_retries=3)])
        try:
            response = await manager.get("https://example.com/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(attempts["n"], 3)
        finally:
            await manager.close()

    async def test_exhausting_retries_surfaces_last_exception(self):
        attempts = {"n": 0}

        def handler(request: httpx.Request) -> httpx.Response:
            attempts["n"] += 1
            return httpx.Response(500, text="fail")

        manager = _make_manager(handler, handlers=[Retry(max_retries=2)])
        try:
            with self.assertRaises(httpx.HTTPStatusError):
                await manager.get("https://example.com/")
            # max_retries=2 means at least 3 attempts should have been made
            # (initial + 2 retries). Without retries actually firing this is 1.
            self.assertGreaterEqual(attempts["n"], 3)
        finally:
            await manager.close()


if __name__ == "__main__":
    unittest.main()
