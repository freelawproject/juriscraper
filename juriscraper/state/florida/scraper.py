"""
Scraper for the Florida unified court API.

Drives :class:`juriscraper.state.RequestManager.RequestManager` against the
public Florida case management API at ``https://acis-api.flcourts.gov`` and
saves raw JSON responses for later parsing/ingestion. Design notes live in
https://github.com/freelawproject/courtlistener/issues/6831.

The scraper is organized around a few concerns:

- Pulling the list of courts at startup and caching their UUIDs in memory so
  later calls can build per-court URLs.
- Paging through ``/courts/cms/cases`` to enumerate cases for a court and date
  range, recursively splitting the range whenever the API reports it has more
  than ``MAX_RESULTS`` matches (the cap is 10,000).
- For each case, pulling case metadata, hearings, parties, and docket entries,
  then pulling the document access record for every docket entry.

Raw responses are written under an output root directory using a layout the
parsers can navigate without round-tripping back to the API:

::

    {output_root}/
        courts.json
        metadata/
            casepartysubtypes.json
            {court_id}/
                casecategories.json
                docketentrysubtypes.json
        {court_id}/
            {case_number}/
                case.json
                hearings.json
                parties.json
                docketentries.json
                docketentrydocuments/
                    {docket_entry_uuid}.json
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import IntEnum
from pathlib import Path
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

# Filename-safe pattern. The API uses case numbers like "4D2026-0606" which
# are already filesystem-friendly, but be defensive about unusual inputs.
_FS_UNSAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _fs_safe(name: str) -> str:
    """Replace filesystem-hostile characters with underscores."""
    return _FS_UNSAFE_RE.sub("_", name)


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
class FloridaScraper:
    """Async scraper for the Florida court API.

    Attributes:
        output_root: Directory under which raw JSON responses are written.
        base_url: API base URL, defaults to the production endpoint.
        rps: Requests per second. Defaults to :data:`DEFAULT_RPS`.
        max_retries: Number of times the :class:`Retry` handler will requeue
            a failed request.
        manager: The configured :class:`RequestManager`. Populated in
            ``__post_init__``.
        courts_by_external_id: Cache of court metadata keyed by the string
            form of ``externalIdentifier``. Populated by
            :meth:`fetch_courts`.
    """

    output_root: Path = field(default_factory=lambda: Path("florida"))
    base_url: str = FLORIDA_API_BASE
    rps: float = DEFAULT_RPS
    max_retries: int = 3
    manager: RequestManager = field(init=False)
    courts_by_external_id: dict[str, FloridaCourt] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Coerce strings/relative paths so callers don't have to.
        self.output_root = Path(self.output_root)
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
    def _write_json(target: Path, payload: Any) -> None:
        """Write ``payload`` to ``target`` as compact JSON.

        Creates parent directories as needed. The output uses no indent and
        the tightest JSON separators we can — the scraper produces a lot of
        small files (one per docket entry, etc.), so storage size wins out
        over diff legibility. Non-ASCII is preserved verbatim.
        """
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as f:
            json.dump(payload, f, separators=(",", ":"), ensure_ascii=False)

    def _case_dir(self, court_external_id: str, case_number: str) -> Path:
        """Resolve the on-disk directory for ``case_number`` in a court."""
        return (
            self.output_root
            / _fs_safe(court_external_id)
            / _fs_safe(case_number)
        )

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
        """Fetch ``/courts``, save the raw response, and cache the result.

        Returns:
            The parsed list of :class:`FloridaCourt`.
        """
        logger.info("Fetching Florida courts list.")
        # The courts endpoint is paginated like everything else, but the
        # current size of the result set (well under 50) lets us request a
        # single page.
        raw = await self._get_json("/courts", params={"size": PAGE_SIZE})
        self._write_json(self.output_root / "courts.json", raw)

        # Validate via the Pydantic model directly. Using the LegacyParser
        # wrapper is overkill here — we already have a parsed dict and don't
        # care about its court_id-keyed API.
        results = FloridaPaginatedResults[FloridaCourt].model_validate(raw)
        courts: list[FloridaCourt] = results.results
        self.courts_by_external_id = {
            str(c.external_identifier): c for c in courts
        }
        logger.info("Fetched %d Florida courts.", len(courts))
        return courts

    async def fetch_metadata(self, court_external_id: str) -> None:
        """Fetch reference metadata for ``court_external_id`` and save it.

        Pulls the global ``/courts/casepartysubtypes`` once per call and the
        per-court ``casecategories`` and ``docketentrysubtypes`` endpoints.

        The data is stored as raw JSON; we don't validate it because parsers
        for these endpoints don't exist yet (and may never need to).
        """
        court = self.courts_by_external_id.get(court_external_id)
        if court is None:
            raise ValueError(
                "Unknown court external id %r — call fetch_courts() first."
                % court_external_id
            )

        meta_dir = (
            self.output_root / "metadata" / _fs_safe(court_external_id)
        )

        casepartysubtypes = await self._get_json("/courts/casepartysubtypes")
        self._write_json(
            self.output_root / "metadata" / "casepartysubtypes.json",
            casepartysubtypes,
        )

        court_uuid = str(court.resource_id)
        casecategories = await self._get_json(
            f"/courts/{court_uuid}/cms/casecategories"
        )
        self._write_json(meta_dir / "casecategories.json", casecategories)

        docketentrysubtypes = await self._get_json(
            f"/courts/{court_uuid}/cms/docketentrysubtypes"
        )
        self._write_json(
            meta_dir / "docketentrysubtypes.json", docketentrysubtypes
        )

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

    async def fetch_case(self, ref: CaseRef) -> None:
        """Fetch and save everything we want for a single case.

        Pulls the case detail endpoint plus paginated hearings, parties, and
        docketentries. For each docket entry, also fetches the document
        access record so we can build download URLs later.
        """
        case_dir = self._case_dir(ref.court_external_id, ref.case_number)

        case_path = f"/courts/{ref.court_uuid}/cms/cases/{ref.case_uuid}"
        case_body = await self._get_json(case_path)
        self._write_json(case_dir / "case.json", case_body)

        # Hearings, parties, and docket entries are all paginated. We save
        # the full ``_embedded.results`` array plus the latest ``page``
        # object so consumers can spot truncation.
        docket_entries: list[dict[str, Any]] = []
        for endpoint in ("hearings", "parties", "docketentries"):
            results, total_elements = await self._fetch_paginated(
                f"{case_path}/{endpoint}",
                params={},
            )
            self._write_json(
                case_dir / f"{endpoint}.json",
                {
                    "_embedded": {"results": results},
                    "page": {
                        "size": PAGE_SIZE,
                        "totalElements": total_elements,
                        "totalPages": 1 if results else 0,
                        "number": 0,
                    },
                },
            )

            if endpoint == "docketentries":
                docket_entries = results

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
            await self.fetch_docket_entry_documents(ref, entry_uuid)

    async def fetch_docket_entry_documents(
        self, ref: CaseRef, docket_entry_uuid: str
    ) -> None:
        """Fetch the document-access record for a docket entry and save it.

        The response contains the ``documentLinkUUID`` and ``documentInfo``
        needed to build per-document download URLs in CourtListener.
        """
        results, total_elements = await self._fetch_paginated(
            "/courts/cms/docketentrydocumentsaccess",
            params={
                "caseHeader.courtID": ref.court_external_id,
                "docketEntryHeader.docketEntryUUID": docket_entry_uuid,
                "caseHeader.caseInstanceUUID": ref.case_uuid,
            },
        )
        target = (
            self._case_dir(ref.court_external_id, ref.case_number)
            / "docketentrydocuments"
            / f"{_fs_safe(docket_entry_uuid)}.json"
        )
        self._write_json(
            target,
            {
                "_embedded": {"results": results},
                "page": {
                    "size": PAGE_SIZE,
                    "totalElements": total_elements,
                    "totalPages": 1 if results else 0,
                    "number": 0,
                },
            },
        )

    # ------------------------------------------------------------------
    # High-level entry point
    # ------------------------------------------------------------------

    async def backfill(
        self,
        court_external_ids: list[str] | None,
        date_range: tuple[date, date],
    ) -> AsyncGenerator[CaseRef, None]:
        """Run the full scrape for ``court_external_ids`` over ``date_range``.

        Fetches courts, then for each court fetches its reference metadata,
        enumerates cases, fetches each one in full, and yields the
        :class:`CaseRef` as a progress signal.

        Args:
            court_external_ids: Subset of courts to scrape, given as the
                ``externalIdentifier`` strings (e.g. ``["1", "2"]``). If
                ``None``, every court in :data:`SCRAPED_COURT_EXTERNAL_IDS`
                that the API actually returns is scraped.
            date_range: Inclusive ``(start, end)`` date pair.
        """
        if not self.courts_by_external_id:
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
                await self.fetch_case(ref)
                yield ref


def run_backfill(
    output_root: str | Path,
    date_range: tuple[date, date],
    court_external_ids: list[str] | None = None,
    rps: float = DEFAULT_RPS,
) -> int:
    """Synchronous entry point for the backfill.

    Returns the number of cases fetched. Intended to be wrapped by a Django
    management command in CourtListener (see CL#7057), but usable standalone
    for local runs.
    """

    async def _drive() -> int:
        count = 0
        async with FloridaScraper(
            output_root=Path(output_root), rps=rps
        ) as scraper:
            async for _ in scraper.backfill(court_external_ids, date_range):
                count += 1
        return count

    return asyncio.run(_drive())
