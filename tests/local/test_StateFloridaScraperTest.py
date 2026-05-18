"""Tests for the Florida scraper driver in ``juriscraper.state.florida.scraper``.

The strategy is the same as the RequestManager tests — swap the client's
transport for an ``httpx.MockTransport`` so requests still travel the real
build/send code path but resolve against an in-process handler. This keeps
tests deterministic without needing a recording layer.
"""

from __future__ import annotations

import json
import unittest
from collections.abc import Callable
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import httpx

from juriscraper.state.florida.scraper import (
    FLORIDA_API_BASE,
    MAX_RESULTS,
    PAGE_SIZE,
    CaseRef,
    FloridaScraper,
    _fs_safe,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _paginated_body(
    results: list[dict[str, Any]] | None = None,
    page: int = 0,
    total_elements: int | None = None,
    page_size: int = PAGE_SIZE,
) -> dict[str, Any]:
    """Build a minimal Florida paginated response body."""
    results = list(results or [])
    if total_elements is None:
        total_elements = len(results)
    total_pages = (
        (total_elements + page_size - 1) // page_size if total_elements else 0
    )
    return {
        "_embedded": {"results": results},
        "page": {
            "size": page_size,
            "totalElements": total_elements,
            "totalPages": total_pages,
            "number": page,
        },
    }


# Hand-crafted v4-compliant UUIDs (version digit = 4, variant = 8/9/a/b).
COURT_1_UUID = "00000001-0000-4000-8000-000000000001"
COURT_5_UUID = "00000005-0000-4000-8000-000000000005"
MOD_USER_UUID_1 = "00000001-0000-4000-8000-00000000aaaa"
MOD_USER_UUID_5 = "00000005-0000-4000-8000-00000000aaaa"


def _courts_body() -> dict[str, Any]:
    """Two courts: Supreme Court (external_id=1) and the 4th DCA (5)."""
    return _paginated_body(
        [
            {
                "active": True,
                "displayName": "Supreme Court of Florida",
                "externalIdentifier": 1,
                "modifiedDate": "2024-01-01T00:00:00.000Z",
                "modifiedUserID": MOD_USER_UUID_1,
                "note": "",
                "resourceID": COURT_1_UUID,
                "locations": [],
            },
            {
                "active": True,
                "displayName": "4th District Court of Appeal",
                "externalIdentifier": 5,
                "modifiedDate": "2024-01-01T00:00:00.000Z",
                "modifiedUserID": MOD_USER_UUID_5,
                "note": "",
                "resourceID": COURT_5_UUID,
                "locations": [],
            },
        ]
    )


def _case_listing_entry(uuid: str, case_number: str) -> dict[str, Any]:
    return {
        "caseHeader": {
            "caseInstanceUUID": uuid,
            "caseNumber": case_number,
            "caseTitle": f"Case {case_number}",
            "closedFlag": False,
            "courtID": "5",
        }
    }


def _docket_entry(uuid: str) -> dict[str, Any]:
    return {"docketEntryHeader": {"docketEntryUUID": uuid}}


# ---------------------------------------------------------------------------
# A scriptable transport
# ---------------------------------------------------------------------------


class _Recorder:
    """Records every path requested and resolves responses via a routing fn.

    Test cases register handlers for specific paths or path prefixes; the
    transport hands back the body the test wants. Anything unrouted returns
    404 so missing handlers are loud rather than silent.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str]]] = []
        self._handlers: list[
            tuple[Callable[[httpx.Request], bool], Callable[[httpx.Request], httpx.Response]]
        ] = []

    def register(
        self,
        predicate: Callable[[httpx.Request], bool],
        handler: Callable[[httpx.Request], httpx.Response],
    ) -> None:
        self._handlers.append((predicate, handler))

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append((request.url.path, dict(request.url.params)))
        for predicate, handler in self._handlers:
            if predicate(request):
                return handler(request)
        return httpx.Response(
            404, json={"error": "no handler", "path": request.url.path}
        )


def _make_scraper(
    output_root: Path, recorder: _Recorder, *, rps: float = 1000.0
) -> FloridaScraper:
    """Build a scraper whose request manager talks to ``recorder``.

    ``rps`` defaults very high so tests don't pay for rate limiting.
    """
    scraper = FloridaScraper(output_root=output_root, rps=rps)
    scraper.manager.client._transport = httpx.MockTransport(recorder)
    return scraper


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class FsSafeTest(unittest.TestCase):
    def test_passthrough_for_safe_names(self):
        self.assertEqual(_fs_safe("4D2026-0606"), "4D2026-0606")
        self.assertEqual(_fs_safe("abc.def_ghi-jkl"), "abc.def_ghi-jkl")

    def test_replaces_path_separators(self):
        self.assertEqual(_fs_safe("a/b\\c"), "a_b_c")

    def test_collapses_runs_of_unsafe_chars(self):
        self.assertEqual(_fs_safe("a   b!!c"), "a_b_c")


class FetchCourtsTest(unittest.IsolatedAsyncioTestCase):
    async def test_fetches_saves_and_caches(self):
        recorder = _Recorder()
        recorder.register(
            lambda r: r.url.path == "/courts",
            lambda r: httpx.Response(200, json=_courts_body()),
        )

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            scraper = _make_scraper(root, recorder)
            try:
                courts = await scraper.fetch_courts()
            finally:
                await scraper.close()

            self.assertEqual(len(courts), 2)
            self.assertIn("1", scraper.courts_by_external_id)
            self.assertIn("5", scraper.courts_by_external_id)

            saved = json.loads((root / "courts.json").read_text())
            self.assertEqual(
                saved["_embedded"]["results"][0]["externalIdentifier"], 1
            )


class FetchMetadataTest(unittest.IsolatedAsyncioTestCase):
    async def test_writes_per_court_and_global_files(self):
        recorder = _Recorder()
        recorder.register(
            lambda r: r.url.path == "/courts",
            lambda r: httpx.Response(200, json=_courts_body()),
        )
        recorder.register(
            lambda r: r.url.path == "/courts/casepartysubtypes",
            lambda r: httpx.Response(200, json=[{"a": 1}]),
        )
        recorder.register(
            lambda r: r.url.path.endswith("/cms/casecategories"),
            lambda r: httpx.Response(200, json=[{"cat": True}]),
        )
        recorder.register(
            lambda r: r.url.path.endswith("/cms/docketentrysubtypes"),
            lambda r: httpx.Response(200, json=[{"sub": True}]),
        )

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            scraper = _make_scraper(root, recorder)
            try:
                await scraper.fetch_courts()
                await scraper.fetch_metadata("5")
            finally:
                await scraper.close()

            self.assertTrue(
                (root / "metadata" / "casepartysubtypes.json").exists()
            )
            self.assertTrue(
                (root / "metadata" / "5" / "casecategories.json").exists()
            )
            self.assertTrue(
                (root / "metadata" / "5" / "docketentrysubtypes.json").exists()
            )

    async def test_unknown_court_raises(self):
        recorder = _Recorder()
        recorder.register(
            lambda r: r.url.path == "/courts",
            lambda r: httpx.Response(200, json=_courts_body()),
        )
        with TemporaryDirectory() as tmp:
            scraper = _make_scraper(Path(tmp), recorder)
            try:
                await scraper.fetch_courts()
                with self.assertRaises(ValueError):
                    await scraper.fetch_metadata("999")
            finally:
                await scraper.close()


class EnumerateCasesTest(unittest.IsolatedAsyncioTestCase):
    async def test_walks_every_page(self):
        # Two pages of 2 results each.
        recorder = _Recorder()
        recorder.register(
            lambda r: r.url.path == "/courts",
            lambda r: httpx.Response(200, json=_courts_body()),
        )

        def case_handler(request: httpx.Request) -> httpx.Response:
            page = int(request.url.params.get("page", "0"))
            all_results = [
                _case_listing_entry(
                    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "4D2026-0001"
                ),
                _case_listing_entry(
                    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "4D2026-0002"
                ),
                _case_listing_entry(
                    "cccccccc-cccc-cccc-cccc-cccccccccccc", "4D2026-0003"
                ),
                _case_listing_entry(
                    "dddddddd-dddd-dddd-dddd-dddddddddddd", "4D2026-0004"
                ),
            ]
            chunk = all_results[page * 2 : (page + 1) * 2]
            return httpx.Response(
                200,
                json=_paginated_body(
                    chunk,
                    page=page,
                    total_elements=4,
                    page_size=2,
                ),
            )

        recorder.register(
            lambda r: r.url.path == "/courts/cms/cases",
            case_handler,
        )

        with TemporaryDirectory() as tmp:
            scraper = _make_scraper(Path(tmp), recorder)
            try:
                await scraper.fetch_courts()
                refs = [
                    ref
                    async for ref in scraper.enumerate_cases(
                        "5", (date(2026, 3, 1), date(2026, 3, 31))
                    )
                ]
            finally:
                await scraper.close()

            self.assertEqual(len(refs), 4)
            self.assertEqual(
                [r.case_number for r in refs],
                [
                    "4D2026-0001",
                    "4D2026-0002",
                    "4D2026-0003",
                    "4D2026-0004",
                ],
            )

    async def test_splits_range_when_total_hits_cap(self):
        recorder = _Recorder()
        recorder.register(
            lambda r: r.url.path == "/courts",
            lambda r: httpx.Response(200, json=_courts_body()),
        )

        seen_ranges: list[tuple[str, str]] = []

        def case_handler(request: httpx.Request) -> httpx.Response:
            params = request.url.params
            page = int(params.get("page", "0"))
            from_param = params.get("caseHeader.filedDateFrom", "")
            to_param = params.get("caseHeader.filedDateTo", "")
            if page == 0:
                seen_ranges.append((from_param, to_param))

            # Original full month reports the cap; the two halves report 1
            # case each.
            if from_param.startswith("2026-03-01") and to_param.startswith(
                "2026-03-31"
            ):
                # First-page peek for the full range: report we're at cap so
                # the scraper subdivides instead of yielding.
                if page == 0:
                    return httpx.Response(
                        200,
                        json=_paginated_body(
                            [], page=0, total_elements=MAX_RESULTS
                        ),
                    )
                return httpx.Response(
                    200, json=_paginated_body([], page=page)
                )

            # Both halves return one distinct case.
            if from_param.startswith("2026-03-01"):
                uuid = "11111111-1111-1111-1111-111111111111"
                number = "4D2026-LO"
            else:
                uuid = "22222222-2222-2222-2222-222222222222"
                number = "4D2026-HI"
            return httpx.Response(
                200,
                json=_paginated_body(
                    [_case_listing_entry(uuid, number)],
                    page=page,
                    total_elements=1,
                ),
            )

        recorder.register(
            lambda r: r.url.path == "/courts/cms/cases",
            case_handler,
        )

        with TemporaryDirectory() as tmp:
            scraper = _make_scraper(Path(tmp), recorder)
            try:
                await scraper.fetch_courts()
                refs = [
                    ref
                    async for ref in scraper.enumerate_cases(
                        "5", (date(2026, 3, 1), date(2026, 3, 31))
                    )
                ]
            finally:
                await scraper.close()

            self.assertEqual(
                sorted(r.case_number for r in refs),
                ["4D2026-HI", "4D2026-LO"],
            )
            # Three first-page queries should have been issued: the full
            # month, then each half.
            self.assertEqual(len(seen_ranges), 3)


class FetchCaseTest(unittest.IsolatedAsyncioTestCase):
    async def test_writes_every_payload_for_a_case(self):
        recorder = _Recorder()

        def case_handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if path.endswith("/cms/cases/CASEUUID"):
                return httpx.Response(200, json={"caseHeader": {}})
            if path.endswith("/hearings"):
                return httpx.Response(200, json=_paginated_body([]))
            if path.endswith("/parties"):
                return httpx.Response(200, json=_paginated_body([]))
            if path.endswith("/docketentries"):
                return httpx.Response(
                    200,
                    json=_paginated_body(
                        [
                            _docket_entry(
                                "deadbeef-0001-0000-0000-000000000000"
                            ),
                            _docket_entry(
                                "deadbeef-0002-0000-0000-000000000000"
                            ),
                        ]
                    ),
                )
            if path == "/courts/cms/docketentrydocumentsaccess":
                return httpx.Response(
                    200,
                    json=_paginated_body(
                        [{"documentLinkUUID": "x", "documentName": "doc"}]
                    ),
                )
            return httpx.Response(404)

        recorder.register(lambda r: True, case_handler)

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            scraper = _make_scraper(root, recorder)
            try:
                await scraper.fetch_case(
                    CaseRef(
                        court_external_id="5",
                        court_uuid=COURT_5_UUID,
                        case_uuid="CASEUUID",
                        case_number="4D2026-0606",
                    )
                )
            finally:
                await scraper.close()

            case_dir = root / "5" / "4D2026-0606"
            self.assertTrue((case_dir / "case.json").exists())
            self.assertTrue((case_dir / "hearings.json").exists())
            self.assertTrue((case_dir / "parties.json").exists())
            self.assertTrue((case_dir / "docketentries.json").exists())
            attachments_dir = case_dir / "docketentrydocuments"
            self.assertTrue(attachments_dir.exists())
            self.assertEqual(
                sorted(p.name for p in attachments_dir.iterdir()),
                [
                    "deadbeef-0001-0000-0000-000000000000.json",
                    "deadbeef-0002-0000-0000-000000000000.json",
                ],
            )

    async def test_skips_docket_entries_without_uuid(self):
        recorder = _Recorder()

        def case_handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if path.endswith("/cms/cases/CASEUUID"):
                return httpx.Response(200, json={"caseHeader": {}})
            if path.endswith("/hearings") or path.endswith("/parties"):
                return httpx.Response(200, json=_paginated_body([]))
            if path.endswith("/docketentries"):
                return httpx.Response(
                    200,
                    json=_paginated_body(
                        [{"docketEntryHeader": {}}]  # missing UUID
                    ),
                )
            if path == "/courts/cms/docketentrydocumentsaccess":
                raise AssertionError(
                    "Should not request docs for an entry with no UUID"
                )
            return httpx.Response(404)

        recorder.register(lambda r: True, case_handler)

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            scraper = _make_scraper(root, recorder)
            try:
                await scraper.fetch_case(
                    CaseRef(
                        court_external_id="5",
                        court_uuid=COURT_5_UUID,
                        case_uuid="CASEUUID",
                        case_number="4D2026-MISSING",
                    )
                )
            finally:
                await scraper.close()

            attachments_dir = (
                root / "5" / "4D2026-MISSING" / "docketentrydocuments"
            )
            self.assertFalse(attachments_dir.exists())


class BackfillTest(unittest.IsolatedAsyncioTestCase):
    async def test_end_to_end_yields_case_refs(self):
        recorder = _Recorder()

        def handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if path == "/courts":
                return httpx.Response(200, json=_courts_body())
            if path == "/courts/casepartysubtypes":
                return httpx.Response(200, json=[])
            if path.endswith("/cms/casecategories"):
                return httpx.Response(200, json=[])
            if path.endswith("/cms/docketentrysubtypes"):
                return httpx.Response(200, json=[])
            if path == "/courts/cms/cases":
                return httpx.Response(
                    200,
                    json=_paginated_body(
                        [
                            _case_listing_entry(
                                "11111111-2222-3333-4444-555555555555",
                                "4D2026-0001",
                            )
                        ]
                    ),
                )
            if path.endswith(
                "/cms/cases/11111111-2222-3333-4444-555555555555"
            ):
                return httpx.Response(200, json={"caseHeader": {}})
            if path.endswith("/hearings"):
                return httpx.Response(200, json=_paginated_body([]))
            if path.endswith("/parties"):
                return httpx.Response(200, json=_paginated_body([]))
            if path.endswith("/docketentries"):
                return httpx.Response(200, json=_paginated_body([]))
            return httpx.Response(404)

        recorder.register(lambda r: True, handler)

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            scraper = _make_scraper(root, recorder)
            try:
                refs = []
                async for ref in scraper.backfill(
                    ["5"], (date(2026, 3, 1), date(2026, 3, 31))
                ):
                    refs.append(ref)
            finally:
                await scraper.close()

            self.assertEqual(len(refs), 1)
            self.assertEqual(refs[0].case_number, "4D2026-0001")
            self.assertTrue((root / "5" / "4D2026-0001" / "case.json").exists())


class FormatDatetimeTest(unittest.TestCase):
    def test_pads_to_zero_time(self):
        self.assertEqual(
            FloridaScraper._format_datetime(date(2026, 3, 5)),
            "2026-03-05T00:00:00.000Z",
        )


class UrlTest(unittest.IsolatedAsyncioTestCase):
    async def test_url_join_handles_missing_slash(self):
        with TemporaryDirectory() as tmp:
            scraper = FloridaScraper(output_root=Path(tmp))
            try:
                self.assertEqual(
                    scraper._url("courts"),
                    f"{FLORIDA_API_BASE}/courts",
                )
                self.assertEqual(
                    scraper._url("/courts"),
                    f"{FLORIDA_API_BASE}/courts",
                )
            finally:
                await scraper.close()


if __name__ == "__main__":
    unittest.main()
