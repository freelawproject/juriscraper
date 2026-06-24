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
from collections.abc import AsyncGenerator, Awaitable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal, TypeVar

import httpx
import pydantic_core
from pydantic import BaseModel, RootModel, ValidationError
from pydantic_core import PydanticCustomError

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
    ExponentialBackoff,
    PrimitiveData,
    RateLimit,
    RequestHandler,
    RequestManager,
    RetryHandler,
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


class PaginationFailed(Exception):
    """Raised when we fail to parse or fetch a page of results from a paginated endpoint.

    Attributes:
        cause: The cause of the failure. One of "network" or "parsing".
        page: The page number that failed.
        url: The endpoint that failed.
        params: The query parameters that were used.
        exc: The exception raised, if any."""

    def __init__(
        self,
        page: int,
        cause: Literal["network"] | Literal["parsing"] | Literal["unknown"],
        url: str,
        params: Mapping[str, PrimitiveData],
        exc: Exception | None = None,
    ) -> None:
        super().__init__(
            "[%s] Paginated fetch of %s with params=%s failed on page %d: %r"
            % (cause.upper(), url, params, page, exc)
        )
        self.cause: str = cause
        self.page: int = page
        self.url: str = url
        self.params: Mapping[str, PrimitiveData] = params
        self.exc: Exception | None = exc


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
        rps: float = 2.5,
        retry: RetryHandler | None = None,
        handlers: list[RequestHandler] | None = None,
    ) -> None:
        """Create a new :class:`FloridaScraper` instance.

        Args:
            rps: Rate-limit for requests
            retry: Retry specification for requests. Defaults to maximum 3 retries with a base sleep of 2 seconds and a growth factor of 2x per retry.
            handlers: Supplementary request handlers to pass to the :class:`RequestManager` instance."""
        if retry is None:
            retry = ExponentialBackoff(
                max_retries=3,
                backoff=2.0,
                backoff_growth=2.0
            )
        self.manager: RequestManager = RequestManager(
            handlers=[
                RateLimit(rps=rps),
            ]
            + (handlers or []),
            retry=retry,
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
                courts_parser.endpoint,
                params=courts_parser.params | {"size": PAGE_SIZE},
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

    async def _enumerate_pages(
        self,
        endpoint: str,
        parser: FloridaPaginatedResultsParser[ResultType],
        params: Mapping[str, PrimitiveData] | None = None,
    ) -> AsyncGenerator[
        FloridaPaginatedResults[ResultType] | PaginationFailed
    ]:
        """Walk every page of a paginated endpoint and yield results.

        Args:
            endpoint: The endpoint to fetch.
            parser: The parser for the endpoint.
            params: Query parameters to pass to the endpoint.

        If the `totalElements` reported by the API is less than the number of elements returned by the endpoint, logs a
        warning after all pages have been iterated.

        If the `totalElements` value changes between pages, logs an error after all pages have been iterated.

        Yields:
            :class:`FloridaPaginatedResults` objects from this endpoint with the specified parameters or
            :class:`PaginationFailed` if the fetch or parse failed.
        """
        if params is None:
            params = {}
        page_params = {"size": PAGE_SIZE, **params}
        totals: set[int] = set()
        actual_total = 0
        errors = 0
        total_pages = 1

        next_page: int = 0
        while next_page < total_pages:
            try:
                body = (
                    await self.manager.get(
                        endpoint, params=page_params | {"page": next_page}
                    )
                ).text
                r = parser.parse_full(body)
                yield r
                totals.add(r.page.total_elements)
                actual_total += len(r.results)
                total_pages = r.page.total_pages
            except httpx.HTTPError as e:
                yield PaginationFailed(
                    next_page, "network", endpoint, page_params, e
                )
                errors += 1
            except (ValidationError, PydanticCustomError, ValueError) as e:
                yield PaginationFailed(
                    next_page, "parsing", endpoint, page_params, e
                )
                errors += 1
            except Exception as e:
                yield PaginationFailed(
                    next_page, "unknown", endpoint, page_params, e
                )
                errors += 1
            next_page += 1

        if len(totals) > 1:
            logger.error(
                "Paginated fetch returned different totalElements across fetches (%s) for %s with params=%s.",
                totals,
                endpoint,
                params,
            )
        if not totals:
            if errors == 0:
                logger.error(
                    "Paginated fetch returned no pages for %s with params=%s",
                    endpoint,
                    params,
                )
            return
        total_elements = totals.pop()
        # Assume every failed page was full to try and avoid noisy logs
        if actual_total + errors * PAGE_SIZE != total_elements:
            logger.error(
                "Actual number of elements returned (%s) does not match totalElements (%s) for %s with params=%s",
                actual_total,
                total_elements,
                endpoint,
                params,
            )

    async def enumerate_cases(
        self,
        court_id: FloridaCourtID,
        start_date: date,
        end_date: date,
    ) -> AsyncGenerator[FloridaCase | PaginationFailed, None]:
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

        Yields:
            :class:`FloridaCase` or :class:`PaginationFailed`

        Raises:
            InsanityException: A single-day query hit :data:`MAX_RESULTS`.
        """
        court_metadata = (await self.courts).get(court_id)
        if court_metadata is None:
            raise ValueError(f"Unknown court id {court_id:r}")
        court_external_id = court_metadata.court.external_identifier
        params = {
            "caseHeader.courtID": str(court_metadata.court.resource_id),
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
            }

            cl_parser = FloridaCaseListParser(court_id=court_id.value)

            pages_aiter = self._enumerate_pages(
                cl_parser.endpoint, cl_parser, params=params
            )

            response = await anext(pages_aiter, None)

            match response:
                case PaginationFailed():
                    yield response
                    continue
                case None:
                    logger.error(
                        "No pages found for %s %s..%s",
                        court_external_id,
                        start,
                        end,
                    )
                    continue
                case FloridaPaginatedResults(page=page) if (
                    page.total_elements >= MAX_RESULTS
                ):
                    if start < end:
                        # Split the range in half and re-queue.
                        mid = start + (end - start) // 2
                        logger.info(
                            "Splitting court %s range %s..%s (totalElements=%d)",
                            court_external_id,
                            start,
                            end,
                            response.page.total_elements,
                        )
                        stack.append((start, mid))
                        stack.append((mid + timedelta(days=1), end))
                        continue
                    # Should be unreachable but who knows.
                    raise InsanityException(
                        "Single-day query for court %s on %s hit the %d-result cap."
                        % (court_id, start, MAX_RESULTS)
                    )

            i = 0
            total = max(response.page.total_elements, 1)
            while response is not None:
                match response:
                    case PaginationFailed():
                        yield response
                    case FloridaPaginatedResults(results=results):
                        for entry in results:
                            yield entry
                            i += 1
                            if i % 100 == 0:
                                logger.info(
                                    "Scraped %d/%d cases from %s..%s for court %s (%.2f%%)",
                                    i,
                                    total,
                                    start,
                                    end,
                                    court_external_id,
                                    i / total * 100,
                                )
                response = await anext(pages_aiter, None)

    async def _flatten_enumerate_pages(
        self,
        endpoint: str,
        parser: FloridaPaginatedResultsParser[ResultType],
        params: Mapping[str, PrimitiveData] | None = None,
    ) -> tuple[list[ResultType], list[PaginationFailed]]:
        """Helper for :meth:`_enumerate_pages` that flattens the results and partitions out :class:`PaginationFailed`
        objects.

        Returns:
            Tuple of the list of results and the list of :class:`PaginationFailed` objects."""
        results: list[ResultType] = []
        errors: list[PaginationFailed] = []

        async for page in self._enumerate_pages(
            endpoint, parser, params=params
        ):
            match page:
                case PaginationFailed():
                    errors.append(page)
                case FloridaPaginatedResults():
                    results.extend(page.results)
        return results, errors

    async def fetch_case_data(
        self, case_uuid: str, court_id: str
    ) -> tuple[FloridaCase, list[PaginationFailed]] | Exception:
        """Fetch unpopulated fields for a Florida case in a given court and return
        a fully populated :class:`FloridaCase` object.

        Pulls the case detail endpoint plus paginated parties and docket
        entries. Also fetches the document access record for each docket entry
        so callers can build download URLs later.

        Returns:
            Tuple of a populated :class:`FloridaCase` object (if there were no failures) and a list of failures that
            occurred. Errors which occur while populating attachments will be logged but will not be propagated. If
            an error occurs while fetching the case details, the return will simply be the exception that occurred.
        """
        fl_court_id = FloridaCourtID(court_id)
        court_data = (await self.courts).get(fl_court_id, None)
        if court_data is None:
            return ValueError(f"{court_id} is not a valid court ID.")
        court_uuid = str(court_data.court.resource_id)

        ci_parser = FloridaCaseInfoParser(court_id=court_id)
        de_parser = FloridaDocketEntryListParser(court_id=court_id)
        parties_parser = FloridaPartyListParser(court_id=court_id)
        arguments_parser = FloridaCaseArgumentsParser(
            court_id=fl_court_id.value
        )

        try:
            case_response = await self.manager.get(
                FloridaCaseInfoParser.endpoint.format(
                    court=court_uuid, case=case_uuid
                )
            )
        except Exception as e:
            return e

        output_case = ci_parser.parse(case_response.text)

        (
            output_case.parties,
            party_errors,
        ) = await self._flatten_enumerate_pages(
            parties_parser.endpoint.format(court=court_uuid, case=case_uuid),
            parties_parser,
        )
        (
            output_case.entries,
            entry_errors,
        ) = await self._flatten_enumerate_pages(
            de_parser.endpoint.format(court=court_uuid, case=case_uuid),
            de_parser,
        )
        (
            output_case.arguments,
            argument_errors,
        ) = await self._flatten_enumerate_pages(
            arguments_parser.endpoint.format(court=court_uuid, case=case_uuid),
            arguments_parser,
        )

        da_parser = FloridaDocumentAccessParser(court_id=court_id)

        da_endpoint_params = {
            "sort": "documentName,asc",
            "caseHeader.courtID": court_uuid,
            "caseHeader.caseInstanceUUID": case_uuid,
        }

        for entry in output_case.entries:
            if entry.document_count > 0:
                (
                    attachments,
                    attachment_errors,
                ) = await self._flatten_enumerate_pages(
                    da_parser.endpoint,
                    da_parser,
                    params=da_endpoint_params
                    | {
                        "docketEntryHeader.docketEntryUUID": str(
                            entry.docket_entry_uuid
                        ),
                    },
                )

                if attachment_errors:
                    logger.error(
                        "Failed to fetch document access records for docket entry %s: %r",
                        entry.docket_entry_uuid,
                        attachment_errors,
                    )
                    continue

                # Sometimes Florida returns "attachments" which have no file we can access and return a 500 if we try to access them
                entry.attachments = [
                    attachment
                    for attachment in attachments
                    if attachment.file_size is not None
                ]

                # We have to compute this here instead of in the parser because it requires the court UUID, which the parser can't access.
                for attachment in entry.attachments:
                    attachment.url = f"{FLORIDA_API_BASE}/courts/{court_uuid}/cms/case/{case_uuid}/docketentrydocuments/{attachment.document_link_uuid}"

        return output_case, party_errors + entry_errors + argument_errors

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

        timespan = end - start

        for court_id in court_ids:
            logger.info(
                "Scraping Florida court %s for %s..%s", court_id, start, end
            )
            i = 0
            async for case in self.enumerate_cases(court_id, start, end):
                if isinstance(case, PaginationFailed):
                    logger.error(
                        "Failed to fetch cases for %s: %s",
                        court_id,
                        case,
                    )
                    continue
                i += 1

                if full_scrape:
                    match await self.fetch_case_data(
                        str(case.case_uuid), case.court_id
                    ):
                        case Exception() as e:
                            logger.error(
                                "Failed to fetch full case data for %s: %s",
                                case.case_uuid,
                                e,
                            )
                        case (_, errors) if errors:
                            logger.error(
                                "Failed to fetch full case data for %s: %r",
                                case.case_uuid,
                                errors,
                            )
                        case (full_case, _):
                            case = full_case

                if i % 1000 == 0:
                    d = case.date_filed
                    logger.info(
                        "Scraped %d cases from %s..%s for court %s. Last date_filed: %s (%.2f%% through date range).",
                        i,
                        start.isoformat(),
                        end.isoformat(),
                        court_id,
                        d.isoformat(),
                        (d - start) / timespan * 100,
                    )
                yield case


async def get_cases(
    start: date, end: date
) -> tuple[dict[FloridaCourtID, CourtMetadata], list[FloridaCase]]:
    """Run the scraper on a given date range"""
    scraper = FloridaScraper(rps=2.5)
    cases = []

    async for case in scraper.backfill(start, end):
        cases.append(case)

    return (await scraper.courts), cases


def _main():
    """Run the scraper on a given date range"""

    import argparse
    import sys
    from datetime import date

    parser = argparse.ArgumentParser(
        prog="Florida Scraper",
        description="Scrape the Florida Supreme Court website for cases in a given date range.",
    )

    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--end", default=date.today().isoformat(), type=date.fromisoformat
    )
    parser.add_argument("--output")

    args = parser.parse_args(sys.argv[1:])

    courts, cases = asyncio.run(get_cases(args.start, args.end))

    if args.output:
        with open(args.output, "wb") as f:
            f.write(
                pydantic_core.to_json(
                    {
                        "courts": courts,
                        "cases": cases,
                    },
                    indent=4,
                )
            )


if __name__ == "__main__":
    _main()
