"""
Scraper for the Florida unified court API.

Drives :class:`juriscraper.state.RequestManager.RequestManager` against the
public Florida case management API at ``https://acis-api.flcourts.gov`` and
yields parsed JSON responses for downstream ingestion. Design notes live in
https://github.com/freelawproject/courtlistener/issues/6831.

The scraper is organized around a few concerns:

- Pulling the list of courts at startup and caching their UUIDs in memory so
  later calls can build per-court URLs. The courts list and per-court
  reference metadata are cached on the instance and hit at most once each
  per scraper lifetime.
- Paging through ``/courts/cms/cases`` to enumerate cases for a court and date
  range, recursively splitting the range whenever the API reports it has more
  than ``MAX_RESULTS`` matches (the cap is 10,000).
- For each case, pulling case metadata, hearings, parties, and docket entries,
  then pulling the document access record for every docket entry.

This module does not persist any data — case-list and per-case payloads are
yielded to the caller (CourtListener) which is responsible for storage.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import IntEnum
from typing import Any

import httpx

from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.state.florida.common import FloridaPaginatedResults
from juriscraper.state.florida.courts import FloridaCourt
from juriscraper.state.RequestManager import (
    RateLimit,
    RequestManager,
    Retry,
)

logger = make_default_logger()

# Public API base URL. Endpoints are appended to this without a trailing slash.
FLORIDA_API_BASE: str = "https://acis-api.flcourts.gov"

# Cases-per-page on the listing endpoints. The API tops out at 50.
PAGE_SIZE: int = 50

# Hard cap on results returned by the API regardless of page size. When a
# search reports this many results, we have to subdivide the query.
MAX_RESULTS: int = 10_000

# Default request rate. Loading a single docket page in the browser triggers
# roughly five JSON requests, so 2.5 rps is the conservative starting point
# agreed on in the design issue.
DEFAULT_RPS: float = 2.5


class ScrapedCourtExternalID(IntEnum):
    """Courts we actively scrape, by ``externalIdentifier`` on ``/courts``.

    Florida county/circuit courts are out of scope — those only appear as
    ``originatingCourtCases`` in appellate dockets, so they're not listed
    here. Adding a new appellate-tier court requires an explicit entry
    here, which is the point: the API silently adding an ID 8 should not
    make us start scraping a court we haven't audited.

    Names mirror the ``displayName`` values returned by the production
    ``/courts`` endpoint (see
    ``tests/examples/state/florida/courts/courts.compare.json``).
    """

    SUPREME_COURT = 1
    FIRST_COA = 2
    SECOND_COA = 3
    THIRD_COA = 4
    FOURTH_COA = 5
    FIFTH_COA = 6
    SIXTH_COA = 7


# Backwards-compatible alias: callers (and the backfill driver) just need a
# membership-testable container of ints. The enum is iterable and its members
# coerce to ints, so ``int(member) in SCRAPED_COURT_EXTERNAL_IDS`` works
# whether we expose the enum class or a derived set.
SCRAPED_COURT_EXTERNAL_IDS: frozenset[int] = frozenset(
    int(m) for m in ScrapedCourtExternalID
)


@dataclass
class CaseRef:
    """Lightweight reference to a case discovered during enumeration.

    Carries just enough information to fetch the full case downstream without
    re-walking the listing endpoint.

    Attributes:
        court_external_id: The court's ``externalIdentifier`` as a string
            (matches the ``caseHeader.courtID`` field on the case).
        court_uuid: The court's ``resourceID`` (UUID), needed to build
            case-scoped URLs.
        case_uuid: The ``caseInstanceUUID`` field from the case header.
        case_number: The human-readable case number (e.g. ``"4D2026-0606"``).
    """

    court_external_id: str
    court_uuid: str
    case_uuid: str
    case_number: str


@dataclass
class CaseData:
    """Full payload for a scraped case, ready for downstream persistence.

    Bundles the discovery :class:`CaseRef` with every parsed JSON body the
    scraper pulled for it. CourtListener decides how to persist these; the
    scraper just hands them over.

    Attributes:
        ref: The :class:`CaseRef` used to fetch this case.
        case: Parsed ``/courts/{court}/cms/cases/{case}`` response body.
        hearings: Concatenated ``_embedded.results`` from the hearings
            endpoint.
        parties: Concatenated ``_embedded.results`` from the parties
            endpoint.
        docket_entries: Concatenated ``_embedded.results`` from the
            docketentries endpoint.
        docket_entry_documents: Mapping of ``docketEntryUUID`` to the
            concatenated ``_embedded.results`` returned by the
            ``/courts/cms/docketentrydocumentsaccess`` endpoint for that
            entry. Entries without a UUID are skipped during the fetch and
            don't appear here.
    """

    ref: CaseRef
    case: dict[str, Any]
    hearings: list[dict[str, Any]]
    parties: list[dict[str, Any]]
    docket_entries: list[dict[str, Any]]
    docket_entry_documents: dict[str, list[dict[str, Any]]]


@dataclass
class CourtMetadata:
    """Reference metadata payloads for a single court.

    Attributes:
        casepartysubtypes: Parsed body of ``/courts/casepartysubtypes`` (this
            is a global endpoint, but we surface it alongside the per-court
            metadata for convenience).
        casecategories: Parsed body of
            ``/courts/{court}/cms/casecategories``.
        docketentrysubtypes: Parsed body of
            ``/courts/{court}/cms/docketentrysubtypes``.
    """

    casepartysubtypes: Any
    casecategories: Any
    docketentrysubtypes: Any


@dataclass
class FloridaScraper:
    """Async scraper for the Florida court API.

    Attributes:
        base_url: API base URL, defaults to the production endpoint.
        rps: Requests per second. Defaults to :data:`DEFAULT_RPS`.
        max_retries: Number of times the :class:`Retry` handler will requeue
            a failed request.
        manager: The configured :class:`RequestManager`. Populated in
            ``__post_init__``.
        courts_by_external_id: Cache of court metadata keyed by the string
            form of ``externalIdentifier``. Populated by
            :meth:`fetch_courts` and reused on subsequent calls.
    """

    base_url: str = FLORIDA_API_BASE
    rps: float = DEFAULT_RPS
    max_retries: int = 3
    manager: RequestManager = field(init=False)
    courts_by_external_id: dict[str, FloridaCourt] = field(default_factory=dict)
    # Single-slot lifetime caches. ``_courts_cache`` holds the parsed list
    # returned by ``fetch_courts``; ``_metadata_cache`` maps a court external
    # id to its :class:`CourtMetadata`. Both are populated lazily and never
    # invalidated within a scraper instance.
    _courts_cache: list[FloridaCourt] | None = field(
        default=None, init=False, repr=False
    )
    _metadata_cache: dict[str, CourtMetadata] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        self.manager = RequestManager(
            handlers=[
                RateLimit(rps=self.rps),
                Retry(max_retries=self.max_retries),
            ]
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Tear down the request manager. Safe to call more than once."""
        await self.manager.close()

    async def __aenter__(self) -> FloridaScraper:
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        """Join ``path`` onto :attr:`base_url`. ``path`` should start with /."""
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    async def _get_json(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a GET, return decoded JSON, and let exceptions propagate.

        Args:
            path: API path. May or may not start with ``/``.
            params: Query parameters to encode onto the URL.

        Returns:
            The decoded JSON body.
        """
        response: httpx.Response = await self.manager.get(
            self._url(path), params=params
        )
        return response.json()

    @staticmethod
    def _format_datetime(d: date) -> str:
        """Format a date for the API's range filters.

        The API expects ISO-8601 with millisecond precision and a ``Z``
        suffix. Bare dates are interpreted as the start of that day in UTC.
        """
        if isinstance(d, datetime):
            dt = d
        else:
            dt = datetime(d.year, d.month, d.day)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # ------------------------------------------------------------------
    # Courts and metadata
    # ------------------------------------------------------------------

    async def fetch_courts(self) -> list[FloridaCourt]:
        """Fetch ``/courts`` once per scraper lifetime, returning the cached
        list on subsequent calls.

        Returns:
            The parsed list of :class:`FloridaCourt`.
        """
        if self._courts_cache is not None:
            return self._courts_cache

        logger.info("Fetching Florida courts list.")
        # The courts endpoint is paginated like everything else, but the
        # current size of the result set (well under 50) lets us request a
        # single page.
        raw = await self._get_json("/courts", params={"size": PAGE_SIZE})

        # Validate via the Pydantic model directly. Using the LegacyParser
        # wrapper is overkill here — we already have a parsed dict and don't
        # care about its court_id-keyed API.
        results = FloridaPaginatedResults[FloridaCourt].model_validate(raw)
        courts: list[FloridaCourt] = results.results
        self.courts_by_external_id = {
            str(c.external_identifier): c for c in courts
        }
        self._courts_cache = courts
        logger.info("Fetched %d Florida courts.", len(courts))
        return courts

    async def fetch_metadata(self, court_external_id: str) -> CourtMetadata:
        """Fetch reference metadata for ``court_external_id``, caching it.

        Pulls the global ``/courts/casepartysubtypes`` and the per-court
        ``casecategories`` and ``docketentrysubtypes`` endpoints. Repeated
        calls for the same court return the cached value without hitting the
        API again.

        The data is returned as raw parsed JSON; we don't validate it
        because parsers for these endpoints don't exist yet (and may never
        need to).
        """
        cached = self._metadata_cache.get(court_external_id)
        if cached is not None:
            return cached

        court = self.courts_by_external_id.get(court_external_id)
        if court is None:
            raise ValueError(
                "Unknown court external id %r — call fetch_courts() first."
                % court_external_id
            )

        casepartysubtypes = await self._get_json("/courts/casepartysubtypes")

        court_uuid = str(court.resource_id)
        casecategories = await self._get_json(
            f"/courts/{court_uuid}/cms/casecategories"
        )
        docketentrysubtypes = await self._get_json(
            f"/courts/{court_uuid}/cms/docketentrysubtypes"
        )

        metadata = CourtMetadata(
            casepartysubtypes=casepartysubtypes,
            casecategories=casecategories,
            docketentrysubtypes=docketentrysubtypes,
        )
        self._metadata_cache[court_external_id] = metadata
        return metadata

    # ------------------------------------------------------------------
    # Case enumeration
    # ------------------------------------------------------------------

    async def _fetch_paginated(
        self,
        path: str,
        params: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], int]:
        """Walk every page of a paginated endpoint and combine results.

        Args:
            path: API path. Must support the ``page``/``size`` parameters.
            params: Additional query parameters (filters, sort, etc.).

        Returns:
            A tuple ``(results, total_elements)``. ``results`` is the
            concatenation of every page's ``_embedded.results`` array.
            ``total_elements`` is the ``page.totalElements`` value reported
            by the API on the first response.

            If the totals don't match (e.g. ``_embedded`` is missing on a
            non-empty page, which the API occasionally does on non-public
            records), a warning is logged and the caller gets whatever was
            collected.
        """
        page = 0
        results: list[dict[str, Any]] = []
        page_params = {"size": PAGE_SIZE, **params}
        total_elements: int | None = None

        while True:
            page_params["page"] = page
            body = await self._get_json(path, params=page_params)
            meta = body.get("page", {})
            if total_elements is None:
                total_elements = int(meta.get("totalElements", 0))

            embedded = body.get("_embedded", {}) or {}
            chunk = embedded.get("results", []) or []
            results.extend(chunk)

            total_pages = int(meta.get("totalPages", 0))
            page += 1
            # Empty page or no more pages — bail out.
            if not chunk or page >= total_pages:
                break

        if total_elements is not None and len(results) != total_elements:
            logger.warning(
                "Paginated fetch returned %d results but API reported "
                "totalElements=%d for %s with params=%s",
                len(results),
                total_elements,
                path,
                params,
            )

        return results, total_elements or 0

    async def enumerate_cases(
        self,
        court_external_id: str,
        date_range: tuple[date, date],
    ) -> AsyncGenerator[CaseRef, None]:
        """Yield :class:`CaseRef` for every case filed in ``date_range``.

        Splits the date range recursively whenever the API reports that the
        query would hit :data:`MAX_RESULTS`. The split is binary on the date
        range — if a single day is over the cap we can't subdivide further,
        so we raise :class:`InsanityException` rather than silently emit a
        truncated result set.

        Args:
            court_external_id: External id of the court (string form of the
                ``externalIdentifier`` field).
            date_range: Inclusive start and end dates.

        Raises:
            InsanityException: A single-day query hit :data:`MAX_RESULTS`,
                so results would be truncated.
        """
        court = self.courts_by_external_id.get(court_external_id)
        if court is None:
            raise ValueError(
                "Unknown court external id %r — call fetch_courts() first."
                % court_external_id
            )
        court_uuid = str(court.resource_id)
        # Stack of (start, end) pairs left to scan. We use a stack instead
        # of recursion so a single yield consumer can drive arbitrarily deep
        # subdivision without growing the call stack.
        stack: list[tuple[date, date]] = [date_range]
        while stack:
            start, end = stack.pop()
            if start > end:
                continue

            params = {
                "caseHeader.courtID": court_external_id,
                "caseHeader.filedDateFrom": self._format_datetime(start),
                "caseHeader.filedDateTo": self._format_datetime(
                    datetime(end.year, end.month, end.day, 23, 59, 59)
                ),
                "sort": "caseHeader.filedDate,asc",
            }

            # Peek at the first page just to check totalElements. We always
            # walk the pages anyway, so issue a real fetch.
            page_params = {"size": PAGE_SIZE, "page": 0, **params}
            first_body = await self._get_json(
                "/courts/cms/cases", params=page_params
            )
            total_elements = int(
                first_body.get("page", {}).get("totalElements", 0)
            )

            if total_elements >= MAX_RESULTS and start < end:
                # Split the range in half and re-queue.
                mid = start + (end - start) // 2
                logger.info(
                    "Splitting court %s range %s..%s (totalElements=%d)",
                    court_external_id,
                    start,
                    end,
                    total_elements,
                )
                stack.append((mid + timedelta(days=1), end))
                stack.append((start, mid))
                continue

            if total_elements >= MAX_RESULTS:
                # Cannot subdivide a single day further — bail loudly so we
                # don't silently undercount. Same pattern as the Texas TAMES
                # scraper (juriscraper/state/texas/tames.py).
                raise InsanityException(
                    "Single-day query for court %s on %s hit the %d-result "
                    "cap; results would be truncated. Unreliable Florida "
                    "scrape."
                    % (court_external_id, start, MAX_RESULTS)
                )

            # Walk every page, starting from the first body we already have.
            page = 0
            total_pages = int(
                first_body.get("page", {}).get("totalPages", 0)
            )
            while True:
                embedded = first_body.get("_embedded", {}) or {}
                results = embedded.get("results", []) or []
                for entry in results:
                    header = entry.get("caseHeader") or {}
                    case_uuid = header.get("caseInstanceUUID")
                    case_number = header.get("caseNumber")
                    if not (case_uuid and case_number):
                        logger.warning(
                            "Skipping case missing UUID or number: %s", entry
                        )
                        continue
                    yield CaseRef(
                        court_external_id=court_external_id,
                        court_uuid=court_uuid,
                        case_uuid=case_uuid,
                        case_number=case_number,
                    )

                page += 1
                if not results or page >= total_pages:
                    break
                page_params["page"] = page
                first_body = await self._get_json(
                    "/courts/cms/cases", params=page_params
                )

    # ------------------------------------------------------------------
    # Single case fetch
    # ------------------------------------------------------------------

    async def fetch_case(self, ref: CaseRef) -> CaseData:
        """Fetch everything we want for a single case and return it.

        Pulls the case detail endpoint plus paginated hearings, parties, and
        docket entries. For each docket entry, also fetches the document
        access record so callers can build download URLs later.

        Returns:
            A :class:`CaseData` bundling every parsed payload alongside the
            originating :class:`CaseRef`.
        """
        case_path = f"/courts/{ref.court_uuid}/cms/cases/{ref.case_uuid}"
        case_body = await self._get_json(case_path)

        # Hearings, parties, and docket entries are all paginated. We keep
        # only the concatenated results arrays — the original pagination
        # metadata isn't useful to consumers once we've drained every page.
        endpoint_results: dict[str, list[dict[str, Any]]] = {}
        for endpoint in ("hearings", "parties", "docketentries"):
            results, _ = await self._fetch_paginated(
                f"{case_path}/{endpoint}",
                params={},
            )
            endpoint_results[endpoint] = results

        docket_entries = endpoint_results["docketentries"]
        docket_entry_documents: dict[str, list[dict[str, Any]]] = {}
        for entry in docket_entries:
            header = entry.get("docketEntryHeader") or {}
            entry_uuid = header.get("docketEntryUUID")
            if not entry_uuid:
                logger.warning(
                    "Skipping docket entry without a UUID in case %s: %s",
                    ref.case_number,
                    entry,
                )
                continue
            docket_entry_documents[entry_uuid] = (
                await self.fetch_docket_entry_documents(ref, entry_uuid)
            )

        return CaseData(
            ref=ref,
            case=case_body,
            hearings=endpoint_results["hearings"],
            parties=endpoint_results["parties"],
            docket_entries=docket_entries,
            docket_entry_documents=docket_entry_documents,
        )

    async def fetch_docket_entry_documents(
        self, ref: CaseRef, docket_entry_uuid: str
    ) -> list[dict[str, Any]]:
        """Fetch the document-access records for a docket entry.

        The response contains the ``documentLinkUUID`` and ``documentInfo``
        needed to build per-document download URLs in CourtListener.

        Returns:
            The concatenated ``_embedded.results`` array across every page.
        """
        results, _ = await self._fetch_paginated(
            "/courts/cms/docketentrydocumentsaccess",
            params={
                "caseHeader.courtID": ref.court_external_id,
                "docketEntryHeader.docketEntryUUID": docket_entry_uuid,
                "caseHeader.caseInstanceUUID": ref.case_uuid,
            },
        )
        return results

    # ------------------------------------------------------------------
    # High-level entry point
    # ------------------------------------------------------------------

    async def backfill(
        self,
        court_external_ids: list[str] | None,
        date_range: tuple[date, date],
    ) -> AsyncGenerator[CaseData, None]:
        """Run the full scrape for ``court_external_ids`` over ``date_range``.

        Fetches courts, then for each court fetches its reference metadata,
        enumerates cases, fetches each one in full, and yields a
        :class:`CaseData` for every case.

        Args:
            court_external_ids: Subset of courts to scrape, given as the
                ``externalIdentifier`` strings (e.g. ``["1", "2"]``). If
                ``None``, every court in :data:`SCRAPED_COURT_EXTERNAL_IDS`
                that the API actually returns is scraped.
            date_range: Inclusive ``(start, end)`` date pair.
        """
        await self.fetch_courts()

        if court_external_ids is None:
            target_ids = [
                eid
                for eid in self.courts_by_external_id
                if int(eid) in SCRAPED_COURT_EXTERNAL_IDS
            ]
        else:
            target_ids = list(court_external_ids)

        for court_external_id in target_ids:
            logger.info(
                "Scraping Florida court %s for %s..%s",
                court_external_id,
                date_range[0],
                date_range[1],
            )
            await self.fetch_metadata(court_external_id)
            async for ref in self.enumerate_cases(
                court_external_id, date_range
            ):
                yield await self.fetch_case(ref)


def run_backfill(
    date_range: tuple[date, date],
    court_external_ids: list[str] | None = None,
    rps: float = DEFAULT_RPS,
) -> int:
    """Synchronous entry point for the backfill.

    Returns the number of cases fetched. Intended to be wrapped by a Django
    management command in CourtListener (see CL#7057), but usable standalone
    for local runs. Yielded :class:`CaseData` is discarded; callers that
    want the payloads should drive :class:`FloridaScraper` directly.
    """

    async def _drive() -> int:
        count = 0
        async with FloridaScraper(rps=rps) as scraper:
            async for _ in scraper.backfill(court_external_ids, date_range):
                count += 1
        return count

    return asyncio.run(_drive())
