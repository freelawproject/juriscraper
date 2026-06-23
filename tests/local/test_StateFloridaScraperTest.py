"""Tests for the Florida scraper driver in ``juriscraper.state.florida.scraper``.

The strategy is the same as the RequestManager tests — swap the client's
transport for an ``httpx.MockTransport`` so requests still travel the real
build/send code path but resolve against an in-process handler. This keeps
tests deterministic without needing a recording layer.
"""

from __future__ import annotations

import unittest
from collections.abc import Callable
from datetime import date
from typing import Any

import httpx

from juriscraper.lib.exceptions import InsanityException
from juriscraper.state.florida.cases import FloridaCase
from juriscraper.state.florida.courts import FloridaCourtID
from juriscraper.state.florida.scraper import (
    MAX_RESULTS,
    PAGE_SIZE,
    CourtMetadata,
    FloridaScraper,
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
CASE_UUID = "562e4de3-c5ea-4e8d-a87f-3c80c4693c70"
DOCKET_ENTRY_UUID_1 = "f09f8909-75f8-427d-a45f-6cdb34182943"
DOCKET_ENTRY_UUID_2 = "5a045473-7a03-4f35-b9ff-f7c0a29f55e8"
PARTY_UUID = "954dcbec-aa08-48bd-bf00-9d41a76e7400"
DOC_LINK_UUID = "1b6a8f72-d404-44e4-8742-5b7e7d38e096"
USER_DOC_STATE_UUID = "b64d1d1e-f926-4c87-ab6b-df5c96d3b186"


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


def _case_party_subtypes_body() -> list[dict[str, Any]]:
    return [
        {
            "participantSubTypeID": 1000005,
            "participantSubTypeName": "Appellant",
            "participantSubTypeComment": "Appellant",
            "participantType": {
                "participantTypeID": 10002,
                "participantTypeName": "Party",
                "participantTypeComment": "Party",
            },
            "involvementType": {
                "casePartyInvolvementTypeID": 10360,
                "casePartyInvolvementTypeValue": "Active",
                "casePartyInvolvementTypeComment": "Active involvement",
            },
        },
    ]


def _case_categories_body() -> list[dict[str, Any]]:
    return [
        {
            "caseCategoryID": 10008,
            "caseCategoryName": "Appeal",
            "caseCategoryComment": "Appellate case",
        },
    ]


def _docket_entry_subtypes_body() -> list[dict[str, Any]]:
    return [
        {
            "docketEntrySubTypeID": 1000074,
            "docketEntrySubTypeName": "Notice of Appeal",
            "docketEntrySubTypeComment": "Notice of Appeal",
            "docketEntryType": {
                "docketEntryTypeID": 1000008,
                "docketEntryTypeName": "Notice",
                "docketEntryTypeComment": "Notice",
            },
        },
    ]


def _case_listing_entry(
    case_uuid: str,
    case_number: str,
    *,
    court_external_id: str = "5",
) -> dict[str, Any]:
    """Minimal payload that satisfies :class:`FloridaCase` validation.

    The case-listing endpoint returns the same envelope as the case-detail
    endpoint, so this fixture is reused for both.
    """
    return {
        "caseHeader": {
            "caseInstanceUUID": case_uuid,
            "caseNumber": case_number,
            "caseTitle": "Case Title v. Other",
            "closedFlag": False,
            "caseClassification": (
                "NOA Final - Circuit Criminal - Habeas Corpus Denial"
            ),
            "caseClassificationID": 1000116,
            "courtID": court_external_id,
            "courtAbbreviation": "4DCA",
            "filedDate": "2026-03-05T16:17:00.000+00:00",
            "originatingCourtCases": [],
        }
    }


def _docket_entry_body(uuid: str) -> dict[str, Any]:
    """Minimal payload that satisfies :class:`FloridaDocketEntry` validation."""
    return {
        "docketEntryHeader": {
            "filedDate": "2026-03-05T16:57:55.000+00:00",
            "docketEntryType": "Notice",
            "docketEntryTypeID": 1000008,
            "docketEntrySubType": "Notice of Appeal",
            "docketEntrySubTypeID": 1000074,
            "docketEntryName": "Notice - Notice of Appeal",
            "submittedDate": "2026-03-04T19:51:04.000+00:00",
            "docketEntryStatusID": 1000000,
            "docketEntryStatus": "Docketed",
            "docketEntryDescription": "Notice of Appeal",
            "official": True,
            "documentCount": 1,
            "securedDocument": True,
            "security1": False,
            "security2": False,
            "security3": False,
            "security4": False,
            "security5": False,
            "compositeSecurity": False,
            "docketEntryUUID": uuid,
        }
    }


def _party_body(uuid: str = PARTY_UUID) -> dict[str, Any]:
    """Minimal payload that satisfies :class:`FloridaParty` validation."""
    return {
        "partyHeader": {
            "casePartyUUID": uuid,
            "partyType": "Party",
            "partyTypeID": 10002,
            "partySubType": "Appellant",
            "partySubTypeID": 1000005,
            "partyStatus": "Active",
            "partyStatusID": 10001,
            "partyActorInstance": {
                "displayName": "Some Person",
                "sortName": "Person, Some",
            },
        },
        "proSeFlag": False,
        "orderBy": 1,
        "legalRepresentations": [],
        "partyNumber": 1,
        "involvementTypeID": 10360,
        "nonPublicFlag": False,
    }


def _document_body(docket_entry_uuid: str) -> dict[str, Any]:
    """Minimal payload that satisfies :class:`FloridaDocument` validation."""
    return {
        "docketEntryUUID": docket_entry_uuid,
        "documentLinkUUID": DOC_LINK_UUID,
        "documentName": "Letter - Acknowledgement Letter",
        "caseHeader": {
            "caseInstanceUUID": CASE_UUID,
            "caseNumber": "4D2026-0606",
            "caseTitle": "Case Title v. Other",
            "courtID": 5,
        },
        "documentInfo": {
            "documentType": "Docket Entry",
            "contentType": "application/pdf",
            "fileExtension": "pdf",
            "pageCount": 6,
            "fileSize": 177522,
        },
        "userDocumentState": USER_DOC_STATE_UUID,
    }


def _hearings_body() -> dict[str, Any]:
    return _paginated_body(
        [
            {
                "startDate": "2023-04-11T18:01:00.000+00:00",
                "hearingType": "Oral Argument",
                "hearingStatus": "Scheduled",
                "event": {"panelFlag": True},
            }
        ]
    )


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
            tuple[
                Callable[[httpx.Request], bool],
                Callable[[httpx.Request], httpx.Response],
            ]
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
    recorder: _Recorder, *, rps: float = 1000.0
) -> FloridaScraper:
    """Build a scraper whose request manager talks to ``recorder``.

    ``rps`` defaults very high so tests don't pay for rate limiting.
    """
    scraper = FloridaScraper(rps=rps)
    scraper.manager._transport = httpx.MockTransport(recorder)
    return scraper


def _register_court_and_metadata_handlers(recorder: _Recorder) -> None:
    """Wire up the four endpoints ``fetch_courts`` reaches for."""
    recorder.register(
        lambda r: r.url.path == "/courts",
        lambda r: httpx.Response(200, json=_courts_body()),
    )
    recorder.register(
        lambda r: r.url.path == "/courts/casepartysubtypes",
        lambda r: httpx.Response(200, json=_case_party_subtypes_body()),
    )
    recorder.register(
        lambda r: r.url.path.endswith("/cms/casecategories"),
        lambda r: httpx.Response(200, json=_case_categories_body()),
    )
    recorder.register(
        lambda r: r.url.path.endswith("/cms/docketentrysubtypes"),
        lambda r: httpx.Response(200, json=_docket_entry_subtypes_body()),
    )
    recorder.register(
        lambda r: r.url.path.endswith("/hearings"),
        lambda r: httpx.Response(200, json=_hearings_body()),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class FetchCourtsTest(unittest.IsolatedAsyncioTestCase):
    async def test_fetches_courts_and_metadata(self):
        recorder = _Recorder()
        _register_court_and_metadata_handlers(recorder)

        async with _make_scraper(recorder) as scraper:
            courts = await scraper.courts

        # Two known courts mapped through FLORIDA_COURT_EXTERNAL_ID_MAP.
        self.assertEqual(len(courts), 2)
        self.assertIn(FloridaCourtID.SUPREME_COURT, courts)
        self.assertIn(FloridaCourtID.FOURTH_COA, courts)

        # Each value is a populated CourtMetadata with parsed lists.
        meta = courts[FloridaCourtID.FOURTH_COA]
        self.assertIsInstance(meta, CourtMetadata)
        self.assertEqual(str(meta.court.resource_id), COURT_5_UUID)
        self.assertEqual(len(meta.case_party_subtypes), 1)
        self.assertEqual(meta.case_party_subtypes[0].name, "Appellant")
        self.assertEqual(len(meta.case_categories), 1)
        self.assertEqual(meta.case_categories[0].name, "Appeal")
        self.assertEqual(len(meta.docket_entry_subtypes), 1)
        self.assertEqual(
            meta.docket_entry_subtypes[0].name, "Notice of Appeal"
        )

    async def test_repeated_calls_hit_api_once(self):
        """fetch_courts should cache for the scraper's lifetime."""
        recorder = _Recorder()
        _register_court_and_metadata_handlers(recorder)

        async with _make_scraper(recorder) as scraper:
            first = await scraper.courts
            second = await scraper.courts
            third = await scraper.courts

        # Same cache object returned on every call.
        self.assertIs(first, second)
        self.assertIs(second, third)

        # Each endpoint should be hit exactly once across the three calls.
        # /courts (global), /courts/casepartysubtypes (global), and a pair
        # of metadata endpoints per court.
        cached_paths = {
            "/courts": 1,
            "/courts/casepartysubtypes": 1,
            f"/courts/{COURT_1_UUID}/cms/casecategories": 1,
            f"/courts/{COURT_1_UUID}/cms/docketentrysubtypes": 1,
            f"/courts/{COURT_5_UUID}/cms/casecategories": 1,
            f"/courts/{COURT_5_UUID}/cms/docketentrysubtypes": 1,
        }
        for path, expected in cached_paths.items():
            actual = sum(1 for c in recorder.calls if c[0] == path)
            self.assertEqual(
                actual,
                expected,
                f"Expected {expected} request(s) to {path}, got {actual}",
            )

    async def test_unknown_external_id_is_skipped(self):
        """Courts whose external_identifier isn't in the map are logged and
        skipped instead of raising."""
        recorder = _Recorder()

        def courts_handler(_request: httpx.Request) -> httpx.Response:
            # Two courts: one known (5) and one with an external id that
            # isn't in FLORIDA_COURT_EXTERNAL_ID_MAP.
            return httpx.Response(
                200,
                json=_paginated_body(
                    [
                        {
                            "active": True,
                            "displayName": "Unknown Court",
                            "externalIdentifier": 999,
                            "modifiedDate": "2024-01-01T00:00:00.000Z",
                            "modifiedUserID": MOD_USER_UUID_1,
                            "note": "",
                            "resourceID": (
                                "99999999-9999-4999-8999-999999999999"
                            ),
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
                ),
            )

        recorder.register(lambda r: r.url.path == "/courts", courts_handler)
        recorder.register(
            lambda r: r.url.path == "/courts/casepartysubtypes",
            lambda r: httpx.Response(200, json=_case_party_subtypes_body()),
        )
        recorder.register(
            lambda r: r.url.path.endswith("/cms/casecategories"),
            lambda r: httpx.Response(200, json=_case_categories_body()),
        )
        recorder.register(
            lambda r: r.url.path.endswith("/cms/docketentrysubtypes"),
            lambda r: httpx.Response(200, json=_docket_entry_subtypes_body()),
        )

        async with _make_scraper(recorder) as scraper:
            courts = await scraper.courts

        # Only the recognized court is cached.
        self.assertEqual(list(courts), [FloridaCourtID.FOURTH_COA])


class EnumerateCasesTest(unittest.IsolatedAsyncioTestCase):
    async def test_yields_parsed_cases_for_range(self):
        recorder = _Recorder()
        _register_court_and_metadata_handlers(recorder)

        def case_handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json=_paginated_body(
                    [
                        _case_listing_entry(
                            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                            "4D2026-0001",
                        ),
                        _case_listing_entry(
                            "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                            "4D2026-0002",
                        ),
                    ],
                    page=0,
                    total_elements=2,
                ),
            )

        recorder.register(
            lambda r: r.url.path == "/courts/cms/cases/",
            case_handler,
        )

        async with _make_scraper(recorder) as scraper:
            await scraper.courts
            cases = [
                c
                async for c in scraper.enumerate_cases(
                    FloridaCourtID.FOURTH_COA,
                    date(2026, 3, 1),
                    date(2026, 3, 31),
                )
            ]

        self.assertEqual(len(cases), 2)
        self.assertIsInstance(cases[0], FloridaCase)
        self.assertEqual(
            [c.docket_number for c in cases],
            ["4D2026-0001", "4D2026-0002"],
        )

    async def test_splits_range_when_total_hits_cap(self):
        recorder = _Recorder()
        _register_court_and_metadata_handlers(recorder)

        page_zero_ranges: list[tuple[str, str]] = []

        def case_handler(request: httpx.Request) -> httpx.Response:
            params = request.url.params
            page = int(params.get("page", "0"))
            from_param = params.get("caseHeader.filedDateFrom", "")
            to_param = params.get("caseHeader.filedDateTo", "")
            if page == 0:
                page_zero_ranges.append((from_param, to_param))

            # Full month reports the cap so the scraper has to subdivide.
            if from_param.startswith("2026-03-01") and to_param.startswith(
                "2026-03-31"
            ):
                return httpx.Response(
                    200,
                    json=_paginated_body(
                        [], page=0, total_elements=MAX_RESULTS
                    ),
                )

            # Each half returns one distinct case.
            if from_param.startswith("2026-03-01"):
                case_uuid = "11111111-1111-4111-8111-111111111111"
                case_number = "4D2026-0001"
            else:
                case_uuid = "22222222-2222-4222-8222-222222222222"
                case_number = "4D2026-0002"

            if page > 0:
                return httpx.Response(
                    200,
                    json=_paginated_body([], page=page, total_elements=1),
                )
            return httpx.Response(
                200,
                json=_paginated_body(
                    [_case_listing_entry(case_uuid, case_number)],
                    page=0,
                    total_elements=1,
                ),
            )

        recorder.register(
            lambda r: r.url.path == "/courts/cms/cases/",
            case_handler,
        )

        async with _make_scraper(recorder) as scraper:
            await scraper.courts
            cases = [
                c
                async for c in scraper.enumerate_cases(
                    FloridaCourtID.FOURTH_COA,
                    date(2026, 3, 1),
                    date(2026, 3, 31),
                )
            ]

        self.assertEqual(
            sorted(c.docket_number for c in cases),
            ["4D2026-0001", "4D2026-0002"],
        )
        # Three first-page queries: the full month, then each half.
        self.assertEqual(len(page_zero_ranges), 3)

    async def test_single_day_overflow_raises(self):
        """A single-day query that hits the cap can't be subdivided."""
        recorder = _Recorder()
        _register_court_and_metadata_handlers(recorder)

        def case_handler(_request: httpx.Request) -> httpx.Response:
            # Every query reports cap; with start == end, no further split.
            return httpx.Response(
                200,
                json=_paginated_body([], page=0, total_elements=MAX_RESULTS),
            )

        recorder.register(
            lambda r: r.url.path == "/courts/cms/cases/",
            case_handler,
        )

        async with _make_scraper(recorder) as scraper:
            await scraper.courts
            with self.assertRaises(InsanityException):
                _ = [
                    c
                    async for c in scraper.enumerate_cases(
                        FloridaCourtID.FOURTH_COA,
                        date(2026, 3, 15),
                        date(2026, 3, 15),
                    )
                ]

    async def test_unknown_court_raises(self):
        """Calling enumerate_cases for a court not in the cache raises."""
        recorder = _Recorder()
        _register_court_and_metadata_handlers(recorder)

        async with _make_scraper(recorder) as scraper:
            await scraper.courts
            with self.assertRaises(ValueError):
                _ = [
                    c
                    async for c in scraper.enumerate_cases(
                        FloridaCourtID.CIRCUIT,  # not returned by /courts
                        date(2026, 3, 1),
                        date(2026, 3, 31),
                    )
                ]


class FetchCaseDataTest(unittest.IsolatedAsyncioTestCase):
    """Tests for :meth:`FloridaScraper.fetch_case_data`."""

    @staticmethod
    def _parse_case(
        case_uuid: str, case_number: str, court_external_id: str = "5"
    ) -> FloridaCase:
        return FloridaCase.model_validate(
            _case_listing_entry(
                case_uuid,
                case_number,
                court_external_id=court_external_id,
            )
        )

    async def test_populates_extra(self):
        recorder = _Recorder()
        _register_court_and_metadata_handlers(recorder)

        recorder.register(
            lambda r: r.url.path.endswith(f"/cases/{CASE_UUID}"),
            lambda r: httpx.Response(
                200,
                json=_case_listing_entry(CASE_UUID, "4D2026-0606"),
            ),
        )

        recorder.register(
            lambda r: r.url.path.endswith("/docketentries"),
            lambda r: httpx.Response(
                200,
                json=_paginated_body(
                    [
                        _docket_entry_body(DOCKET_ENTRY_UUID_1),
                        _docket_entry_body(DOCKET_ENTRY_UUID_2),
                    ],
                    total_elements=2,
                ),
            ),
        )

        recorder.register(
            lambda r: r.url.path.endswith(f"/cases/{CASE_UUID}/parties"),
            lambda r: httpx.Response(
                200,
                json=_paginated_body([_party_body()], total_elements=1),
            ),
        )

        def docs_handler(request: httpx.Request) -> httpx.Response:
            entry_uuid = request.url.params.get(
                "docketEntryHeader.docketEntryUUID", ""
            )
            return httpx.Response(
                200,
                json=_paginated_body(
                    [_document_body(entry_uuid)],
                    total_elements=1,
                ),
            )

        recorder.register(
            lambda r: r.url.path == "/courts/cms/docketentrydocumentsaccess",
            docs_handler,
        )

        async with _make_scraper(recorder) as scraper:
            await scraper.courts
            case = self._parse_case(CASE_UUID, "4D2026-0606")
            populated, errors = await scraper.fetch_case_data(
                str(case.case_uuid), case.court_id
            )

        # Returned object is a populated copy of the case we passed in.
        self.assertEqual(len(errors), 0)
        self.assertIsInstance(populated, FloridaCase)
        self.assertEqual(populated.docket_number, "4D2026-0606")
        self.assertEqual(len(populated.parties), 1)
        self.assertEqual(str(populated.parties[0].party_uuid), PARTY_UUID)
        self.assertEqual(len(populated.entries), 2)
        entry_uuids = sorted(
            str(e.docket_entry_uuid) for e in populated.entries
        )
        self.assertEqual(
            entry_uuids, sorted([DOCKET_ENTRY_UUID_1, DOCKET_ENTRY_UUID_2])
        )
        # Each docket entry pulled its own document-access record.
        for entry in populated.entries:
            self.assertEqual(len(entry.attachments), 1)
            self.assertEqual(
                str(entry.attachments[0].docket_entry_uuid),
                str(entry.docket_entry_uuid),
            )


class BackfillTest(unittest.IsolatedAsyncioTestCase):
    async def test_yields_cases_for_each_court_in_range(self):
        """``backfill`` should drive courts → enumerate → yield cases.

        Uses ``full_scrape=False`` so the test doesn't depend on the
        currently-broken :meth:`fetch_case_data` path (see report).
        ``full_scrape=True`` end-to-end coverage will be added once the
        court-id lookup is fixed.
        """
        recorder = _Recorder()
        _register_court_and_metadata_handlers(recorder)

        def case_listing_handler(request: httpx.Request) -> httpx.Response:
            page = int(request.url.params.get("page", "0"))
            if page > 0:
                return httpx.Response(
                    200,
                    json=_paginated_body(
                        [], page=page, total_elements=1, page_size=PAGE_SIZE
                    ),
                )
            return httpx.Response(
                200,
                json=_paginated_body(
                    [_case_listing_entry(CASE_UUID, "4D2026-0606")],
                    total_elements=1,
                ),
            )

        recorder.register(
            lambda r: r.url.path == "/courts/cms/cases/",
            case_listing_handler,
        )

        async with _make_scraper(recorder) as scraper:
            cases = []
            async for case in scraper.backfill(
                date(2026, 3, 1),
                date(2026, 3, 31),
                court_ids=[FloridaCourtID.FOURTH_COA],
                full_scrape=False,
            ):
                cases.append(case)

        self.assertEqual(len(cases), 1)
        self.assertIsInstance(cases[0], FloridaCase)
        self.assertEqual(cases[0].docket_number, "4D2026-0606")

    async def test_full_scrape_false_skips_case_detail_fetch(self):
        """``full_scrape=False`` should yield list-level cases without
        hitting the per-case endpoints."""
        recorder = _Recorder()
        _register_court_and_metadata_handlers(recorder)

        def case_listing_handler(request: httpx.Request) -> httpx.Response:
            page = int(request.url.params.get("page", "0"))
            if page > 0:
                return httpx.Response(
                    200,
                    json=_paginated_body(
                        [], page=page, total_elements=1, page_size=PAGE_SIZE
                    ),
                )
            return httpx.Response(
                200,
                json=_paginated_body(
                    [_case_listing_entry(CASE_UUID, "4D2026-0606")],
                    total_elements=1,
                ),
            )

        recorder.register(
            lambda r: r.url.path == "/courts/cms/cases/",
            case_listing_handler,
        )
        # Loud failures if we hit per-case endpoints.
        recorder.register(
            lambda r: (
                r.url.path.endswith("/docketentries")
                or r.url.path.endswith("/parties")
                or r.url.path == "/courts/cms/docketentrydocumentsaccess"
            ),
            lambda r: httpx.Response(500, text="should not be called"),
        )

        async with _make_scraper(recorder) as scraper:
            cases = []
            async for case in scraper.backfill(
                date(2026, 3, 1),
                date(2026, 3, 31),
                court_ids=[FloridaCourtID.FOURTH_COA],
                full_scrape=False,
            ):
                cases.append(case)

        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0].docket_number, "4D2026-0606")
        # Verify we never hit the per-case endpoints.
        per_case_paths = {"/docketentries", "/parties"}
        for path, _params in recorder.calls:
            self.assertFalse(
                any(path.endswith(suffix) for suffix in per_case_paths),
                f"backfill(full_scrape=False) hit per-case path {path}",
            )


class LifecycleTest(unittest.IsolatedAsyncioTestCase):
    async def test_async_context_manager_closes(self):
        recorder = _Recorder()
        recorder.register(
            lambda r: True,
            lambda r: httpx.Response(200, text="ok"),
        )
        async with FloridaScraper(rps=1000.0) as scraper:
            scraper.manager._transport = httpx.MockTransport(recorder)
            self.assertFalse(scraper.manager.is_closed)
        self.assertTrue(scraper.manager.is_closed)

    async def test_close_is_idempotent(self):
        async with FloridaScraper(rps=1000.0) as scraper:
            self.assertFalse(scraper.manager.is_closed)
        self.assertTrue(scraper.manager.is_closed)
