# Scraper for Florida Supreme Court
# CourtID: fla
# Court Short Name: fla

from datetime import date, datetime, timedelta
from math import ceil
from typing import NotRequired
from urllib.parse import urljoin

from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import RequestParameters, SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class _Document(TypedDict):
    uri: str


class _DateValue(TypedDict):
    date: str


class _DispositionDate(TypedDict):
    date: _DateValue


class _Fields(TypedDict):
    case_number: str
    disposition_date: _DispositionDate
    note: NotRequired[str | None]
    disposition: NotRequired[str | None]
    case_style: str
    opinion: _Document


class _Content(TypedDict):
    fields: dict[str, object]


class _Result(TypedDict):
    content: _Content


class _Search(TypedDict):
    totalCount: int
    searchResults: list[_Result]


_search_adapter = TypeAdapter(_Search)
_fields_adapter = TypeAdapter(_Fields)


class Site(OpinionSiteLinear[tuple[date, date]]):
    start_date: date
    end_date: date

    days_interval = 20
    # Days to look back on a regular scrape, kept short to bound pagination
    scrape_interval = 30
    first_opinion_date = datetime(1999, 9, 23)
    # you can put whatever number you want as limit, 100 seems to be the max
    page_size = 100
    base_url = "https://flcourts-media.flcourts.gov/_search/opinions/?limit={}&offset={}&query=&scopes[]={}&searchtype=opinions&siteaccess={}&startdate={}&enddate={}"
    scopes = "supreme_court"
    site_access = "supreme2"
    # Example built URL
    # "https://flcourts-media.flcourts.gov/_search/opinions/?limit=100&offset=0&query=&scopes[]=supreme_court&searchtype=opinions&siteaccess=supreme2&startdate=2025-07-01&enddate=2026-01-01"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.set_url()
        self.make_backscrape_iterable(kwargs)

    @override
    async def _download(
        self, request_dict: RequestParameters | None = None
    ) -> _Search:
        """Download every page of results for the current date range

        The source returns results sorted by
        `disposition_date desc, case_number asc`.

        :param request_dict: passed through to the parent downloader
        :return: the first page's JSON, with all the pages' `searchResults`
        """
        first_page = _search_adapter.validate_python(
            await super()._download(request_dict), strict=True
        )
        if self.test_mode_enabled():
            return first_page

        total_count = first_page["totalCount"]
        results = first_page["searchResults"]
        first_page_url = self.url

        for page in range(1, ceil(total_count / self.page_size)):
            self.url = self.build_url(page * self.page_size)
            page_results = _search_adapter.validate_python(
                await super()._download(request_dict), strict=True
            )["searchResults"]
            results.extend(page_results)

            if len(page_results) < self.page_size:
                # Last page of results; a further offset returns 404
                break

        if len(results) < total_count:
            logger.error(
                "%s: got %s of %s results reported by the source for %s. Some opinions were not scraped",
                self.court_id,
                len(results),
                total_count,
                first_page_url,
            )

        self.url = first_page_url
        first_page["searchResults"] = results

        return first_page

    @override
    def _process_html(self) -> None:
        """Parses HTML into case dictionaries

        :return: None
        """
        json = _search_adapter.validate_python(self.html, strict=True)
        for row in json["searchResults"]:
            raw_fields = row["content"]["fields"]
            if raw_fields.get("note") in ("Notice of Correction",):
                logger.info("Skipping non-opinion document %s", raw_fields)
                continue

            if not bool(raw_fields.get("case_style")):
                # These seem to be family - children related cases. See example
                # in district 4 example file
                # https://flcourts-media.ccplatform.net/content/download/2472477/28965542?version=5
                logger.info("Skipping case with no name %s", raw_fields)
                continue

            if not bool(raw_fields.get("opinion")):
                # Some rows are orders by a clerk / judge, which have no
                # opinion doc (3DCA 2022-0306). Others are opinions whose file
                # is missing (2DCA 2024-0481)
                logger.info(
                    "Skipping case with no opinion file %s",
                    raw_fields.get("case_number"),
                )
                continue

            fields = _fields_adapter.validate_python(raw_fields, strict=True)
            # `note` and `disposition` may come back as JSON null, in which
            # case `fields.get(..., "")` returns None instead of the default.
            note = fields.get("note")
            if note is None:
                note = ""
            disposition = fields.get("disposition")
            if disposition is None:
                disposition = ""
            self.cases.append(
                {
                    "url": urljoin(self.base_url, fields["opinion"]["uri"]),
                    "docket": self.get_docket_number(fields["case_number"]),
                    "name": titlecase(fields["case_style"]),
                    "date": fields["disposition_date"]["date"]["date"].split(
                        " "
                    )[0],
                    "disposition": self.get_disposition(disposition, note),
                    "status": self.status,
                    "per_curiam": "per curiam" in disposition.lower(),
                }
            )

    def get_docket_number(self, raw_docket_number: str) -> str:
        """Prepend the district code to a docket number

        This is useful to disambiguate district court of appeals docket numbers

        :param raw_docket_number: the docket number as returned by the source
        :return: the clean docket number
        """
        return raw_docket_number

    def get_disposition(self, raw_disposition: str, note: str) -> str:
        """Get a valid disposition value from raw values

        :param raw_disposition: the raw disposition in the returned json
        :param note: a value in the return json that may contain a disposition
        return: A clean disposition value
        """
        return titlecase(raw_disposition)

    def set_url(
        self, start: date | None = None, end: date | None = None
    ) -> None:
        """Sets the first page URL using date arguments

        :param start: start date; defaults to `scrape_interval` days before
            the end date
        :param end: end date; defaults to today
        :return: none
        """
        if end is None:
            end = datetime.today()
        if start is None:
            start = end - timedelta(days=self.scrape_interval)

        self.start_date = start
        self.end_date = end
        self.url = self.build_url()

    def build_url(self, offset: int = 0) -> str:
        """Builds the URL of a single results page

        :param offset: index of the first result to return.
        :return: the page URL
        """
        fmt = "%Y-%m-%d"
        return self.base_url.format(
            self.page_size,
            offset,
            self.scopes,
            self.site_access,
            self.start_date.strftime(fmt),
            self.end_date.strftime(fmt),
        )

    @override
    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Overrides scraper URL using date inputs

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.set_url(*dates)
        logger.info("Backscraping for range %s %s", *dates)
