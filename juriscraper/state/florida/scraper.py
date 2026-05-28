"""Scraper for the Florida court API.

Drives :class:`juriscraper.state.RequestManager.RequestManager` against the
public Florida case management API at ``https://acis-api.flcourts.gov`` and
yields parsed JSON responses for downstream ingestion. Design notes live in
https://github.com/freelawproject/courtlistener/issues/6831.

The scraper is organized around a few concerns:

- Pulling the list of courts at startup and caching their UUIDs in memory so
  later calls can build per-court URLs. The court list and per-court
  reference metadata are cached on the instance and hit at most once each
  per scraper lifetime.
- Paging through ``/courts/cms/cases`` to enumerate cases for a court and date
  range, recursively splitting the range whenever the API reports it has more
  than ``MAX_RESULTS`` matches (the cap is 10,000).
- For each case, pulling case metadata, hearings, parties, and docket entries,
  then pulling the document access record for every docket entry.

This module does not persist any data — case-list and per-case payloads are
yielded to the caller which is responsible for storage.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Awaitable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from itertools import chain
from typing import TypeVar

from pydantic import BaseModel, RootModel

from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.state.florida import FloridaCaseListParser
from juriscraper.state.florida.arguments import FloridaCaseArgumentsParser
from juriscraper.state.florida.cases import (
    FloridaCase,
    FloridaCaseInfoParser,
)
from juriscraper.state.florida.common import (
    FloridaPaginatedResults,
    FloridaPaginatedResultsParser,
)
from juriscraper.state.florida.courts import (
    FLORIDA_COURT_EXTERNAL_ID_MAP,
    FloridaCourt,
    FloridaCourtID,
    FloridaCourtsParser,
)
from juriscraper.state.florida.docket_entries import (
    FloridaDocketEntryListParser,
)
from juriscraper.state.florida.documents import FloridaDocumentAccessParser
from juriscraper.state.florida.metadata import (
    CaseCategory,
    CasePartySubType,
    DocketEntrySubType,
)
from juriscraper.state.florida.parties import FloridaPartyListParser
from juriscraper.state.RequestManager import (
    PrimitiveData,
    RateLimit,
    RequestHandler,
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

T = TypeVar("T", bound=BaseModel)


@dataclass
class CourtMetadata:
    """Reference metadata payloads for a single court.

    Attributes:
        court: One parsed entry from the ``/courts`` endpoint.
        case_party_subtypes: Parsed body of ``/courts/casepartysubtypes`` (this
            is a global endpoint, but we surface it alongside the per-court
            metadata for convenience).
        case_categories: Parsed body of ``/courts/{court}/cms/casecategories``.
        docket_entry_subtypes: Parsed body of ``/courts/{court}/cms/docketentrysubtypes``.
    """

    court: FloridaCourt
    case_party_subtypes: list[CasePartySubType]
    case_categories: list[CaseCategory]
    docket_entry_subtypes: list[DocketEntrySubType]


ResultType = TypeVar("ResultType", bound=BaseModel)


class FloridaScraper:
    """Async scraper for the Florida court API.

    Attributes:
        manager: The configured :class:`RequestManager` with rate-limiting and retries.
        courts: Cached :class:`FloridaCourt` objects and their metadata.
    """

    def __init__(
        self,
        *,
        rps: float | None = None,
        max_retries: int | None = None,
        handlers: list[RequestHandler] | None = None,
    ) -> None:
        """Create a new :class:`FloridaScraper` instance.

        Args:
            handlers: Supplementary request handlers to pass to the :class:`RequestManager` instance."""
        self.manager: RequestManager = RequestManager(
            handlers=[
                RateLimit(rps=rps or 2.5),
                Retry(max_retries=max_retries or 3),
            ]
            + (handlers or []),
            base_url=FLORIDA_API_BASE,
        )
        self._courts_future: (
            asyncio.Future[dict[FloridaCourtID, CourtMetadata]] | None
        ) = None

    async def __aenter__(self) -> FloridaScraper:
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        await self.manager.aclose()

    @property
    def courts(
        self,
    ) -> Awaitable[dict[FloridaCourtID, CourtMetadata]]:
        """Awaitable resolving to the cached courts dict.

        The first ``await`` triggers the fetch; concurrent and subsequent
        awaits share the same in-flight task and resolve to the same dict.
        """
        if self._courts_future is None:
            self._courts_future = asyncio.ensure_future(self._fetch_courts())
        return self._courts_future

    async def _fetch_courts(
        self,
    ) -> dict[FloridaCourtID, CourtMetadata]:
        """Fetch court and metadata endpoints once per scraper lifetime."""
        logger.info("Fetching Florida courts list.")
        # The courts endpoint is paginated like everything else, but the
        # current size of the result set (well under 50) lets us request a
        # single page.
        courts_parser = FloridaCourtsParser(court_id="fl")
        raw = (
            await self.manager.get(
                courts_parser.endpoint, params={"size": PAGE_SIZE}
            )
        ).text
        court_results = courts_parser.parse(raw)

        case_party_subtypes = (
            RootModel[list[CasePartySubType]]
            .model_validate_json(
                (await self.manager.get("/courts/casepartysubtypes")).text
            )
            .root
        )

        courts: dict[FloridaCourtID, CourtMetadata] = {}

        for court in court_results:
            e_id = str(court.external_identifier)
            if e_id not in FLORIDA_COURT_EXTERNAL_ID_MAP:
                logger.error(
                    "Found unknown court %r with unknown external id %s",
                    court,
                    e_id,
                )
                continue
            court_id = FLORIDA_COURT_EXTERNAL_ID_MAP[e_id]
            logger.info("Fetching metadata for %s", court_id)
            case_categories = (
                RootModel[list[CaseCategory]]
                .model_validate_json(
                    (
                        await self.manager.get(
                            f"/courts/{court.resource_id}/cms/casecategories"
                        )
                    ).text
                )
                .root
            )
            docket_entry_subtypes = (
                RootModel[list[DocketEntrySubType]]
                .model_validate_json(
                    (
                        await self.manager.get(
                            f"/courts/{court.resource_id}/cms/docketentrysubtypes"
                        )
                    ).text
                )
                .root
            )
            courts[court_id] = CourtMetadata(
                court=court,
                case_party_subtypes=case_party_subtypes,
                case_categories=case_categories,
                docket_entry_subtypes=docket_entry_subtypes,
            )
            logger.info("Metadata for %s cached.", court_id)
        logger.info("Fetched %d Florida courts.", len(court_results))
        return courts

    async def _fetch_paginated(
        self,
        endpoint: str,
        parser: FloridaPaginatedResultsParser[ResultType],
        params: dict[str, PrimitiveData] | None = None,
    ) -> list[FloridaPaginatedResults[ResultType]]:
        """Walk every page of a paginated endpoint and combine results.

        Args:
            endpoint: The endpoint to fetch.
            parser: The parser for the endpoint.
            params: Query parameters to pass to the endpoint.

        If the `totalElements` reported by the API is less than the number of
        elements returned by the endpoint, logs a warning.

        If the `totalElements` value changes between pages, logs an error.

        Returns:
            The full list of :class:`FloridaPaginatedResults` objects for this
            endpoint with the specified parameters.
        """
        if params is None:
            params = {}
        results: list[FloridaPaginatedResults[ResultType]] = []
        page_params = {"size": PAGE_SIZE, **params}

        next_page: int | None = 0
        while next_page is not None:
            page_params["page"] = next_page
            body = (await self.manager.get(endpoint, params=page_params)).text
            r = parser.parse_full(body)
            results.append(r)
            if next_page + 1 < r.page.total_pages:
                next_page += 1
            else:
                next_page = None

        totals = {r.page.total_elements for r in results}
        if len(totals) > 1:
            logger.error(
                f"Paginated fetch returned different totalElements across fetches ({totals})."
            )
        total_elements = totals.pop()
        actual_total = sum(len(r.results) for r in results)
        if actual_total != total_elements:
            logger.error(
                f"Actual number of elements returned ({actual_total}) does not match totalElements ({total_elements}) for {parser.endpoint} with params={params}"
            )

        return results

    async def enumerate_cases(
        self,
        court_id: FloridaCourtID,
        start_date: date,
        end_date: date,
    ) -> AsyncGenerator[FloridaCase, None]:
        """Yield :class:`FloridaCase` for every case filed in ``date_range``.

        Splits the date range recursively whenever the API reports that the
        query would hit :data:`MAX_RESULTS`. The split is binary on the date
        range. If a single day is over the cap we can't subdivide further,
        so we raise :class:`InsanityException` rather than silently emit a
        truncated result set.

        Args:
            court_id: ID of the court.
            start_date: Start of the date range.
            end_date: End of the date range.

        Raises:
            InsanityException: A single-day query hit :data:`MAX_RESULTS`.
        """
        court_metadata = (await self.courts).get(court_id)
        if court_metadata is None:
            raise ValueError(f"Unknown court id %r {court_id}")
        court_external_id = court_metadata.court.external_identifier
        params = {
            "size": PAGE_SIZE,
            "caseHeader.courtID": court_external_id,
            "sort": "caseHeader.filedDate,asc",
        }

        stack: list[tuple[date, date]] = [(start_date, end_date)]
        while stack:
            start, end = stack.pop()
            params |= {
                "caseHeader.filedDateFrom": datetime(
                    start.year, start.month, start.day
                ).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "caseHeader.filedDateTo": datetime(
                    end.year, end.month, end.day, 23, 59, 59
                ).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "page": 0,
            }

            cl_parser = FloridaCaseListParser(court_id=court_id.value)

            response = await self.manager.get(
                cl_parser.endpoint, params=params
            )

            response_page = cl_parser.parse_full(response.text)

            if response_page.page.total_elements >= MAX_RESULTS:
                if start < end:
                    # Split the range in half and re-queue.
                    mid = start + (end - start) // 2
                    logger.info(
                        "Splitting court %s range %s..%s (totalElements=%d)",
                        court_external_id,
                        start,
                        end,
                        response_page.page.total_elements,
                    )
                    stack.append((start, mid))
                    stack.append((mid + timedelta(days=1), end))
                    continue
                # Should be unreachable but who knows.
                raise InsanityException(
                    "Single-day query for court %s on %s hit the %d-result cap."
                    % (court_external_id, start, MAX_RESULTS)
                )

            # Walk every page, starting from the first body we already have.
            while True:
                for entry in response_page.results:
                    yield entry
                if (
                    response_page.page.page_number + 1
                    >= response_page.page.total_pages
                ):
                    break
                response = await self.manager.get(
                    cl_parser.endpoint,
                    params=params
                    | {"page": response_page.page.page_number + 1},
                )
                response_page = cl_parser.parse_full(response.text)

    async def fetch_case_data(self, case: FloridaCase) -> FloridaCase:
        """Fetch unpopulated fields for a :class:`FloridaCase` object and return
        a populated copy.

        Pulls the case detail endpoint plus paginated parties and docket
        entries. Also fetches the document access record for each docket entry
        so callers can build download URLs later.

        Returns:
            A populated :class:`FloridaCase` object
        """
        court_id = FloridaCourtID(case.court_id)
        court_data = (await self.courts).get(court_id, None)
        if court_data is None:
            raise ValueError(f"{case.court_id} is not a valid court ID.")
        court_uuid = court_data.court.resource_id
        case_uuid = case.case_uuid

        ci_parser = FloridaCaseInfoParser(court_id=court_id.value)
        de_parser = FloridaDocketEntryListParser(court_id=court_id.value)
        parties_parser = FloridaPartyListParser(court_id=court_id.value)
        arguments_parser = FloridaCaseArgumentsParser(court_id=court_id.value)

        case_response = await self.manager.get(
            FloridaCaseInfoParser.endpoint.format(
                court=court_uuid, case=case_uuid
            )
        )

        output_case = ci_parser.parse(case_response.text)

        docket_entry_pages = await self._fetch_paginated(
            de_parser.endpoint.format(court=court_uuid, case=case_uuid),
            de_parser,
        )

        parties_pages = await self._fetch_paginated(
            parties_parser.endpoint.format(court=court_uuid, case=case_uuid),
            parties_parser,
        )

        arguments_pages = await self._fetch_paginated(
            arguments_parser.endpoint.format(court=court_uuid, case=case_uuid),
            arguments_parser,
        )

        output_case.parties = list(
            chain.from_iterable(p.results for p in parties_pages)
        )
        output_case.entries = list(
            chain.from_iterable(p.results for p in docket_entry_pages)
        )
        output_case.arguments = list(
            chain.from_iterable(p.results for p in arguments_pages)
        )

        court_external_id = court_data.court.external_identifier

        da_parser = FloridaDocumentAccessParser(court_id=court_id.value)

        for entry in output_case.entries:
            document_pages = await self._fetch_paginated(
                da_parser.endpoint,
                da_parser,
                params={
                    "caseHeader.courtID": court_external_id,
                    "docketEntryHeader.docketEntryUUID": str(
                        entry.docket_entry_uuid
                    ),
                    "caseHeader.caseInstanceUUID": str(case_uuid),
                },
            )

            entry.attachments = list(
                chain.from_iterable(p.results for p in document_pages)
            )

        return output_case

    async def backfill(
        self,
        start: date,
        end: date,
        *,
        court_ids: list[FloridaCourtID] | None = None,
        full_scrape: bool = True,
    ) -> AsyncGenerator[FloridaCase, None]:
        """Run the full scrape for ``court_ids`` over ``date_range``.

        Fetches courts, then for each court fetches its reference metadata,
        enumerates cases, fetches each one in full, and yields a
        :class:`CaseData` for every case.

        Args:
            start: Date to begin the scape at.
            end: Date to end the scrape on.
            court_ids: Subset of courts to scrape. If not provided, all courts
                will be scraped.
            full_scrape: If ``True``, fetches the case list and full case details
                for every case in every court in the date range. Otherwise, only
                fetches the case list.
        """
        _ = await self.courts

        if court_ids is None:
            court_ids = list((await self.courts or {}).keys())

        for court_id in court_ids:
            logger.info(
                f"Scraping Florida court {court_id} for {start}..{end}"
            )
            async for case in self.enumerate_cases(court_id, start, end):
                if full_scrape:
                    case = await self.fetch_case_data(case)
                yield case
