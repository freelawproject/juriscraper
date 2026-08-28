# Scraper for Florida Supreme Court
# CourtID: fla
# Court Short Name: fla

from datetime import date, datetime, timedelta
from math import ceil
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.set_url()
        self.make_backscrape_iterable(kwargs)

    async def _download(self, request_dict=None):
        """Download every page of results for the current date range

        The source returns at most `page_size` results per request, sorted
        by `disposition_date desc, case_number asc`. Without pagination,
        every opinion past the first page is silently dropped. See #2150

        :param request_dict: passed through to the parent downloader
        :return: the first page's JSON, with all the pages' `searchResults`
        """
        first_page = await super()._download(request_dict)
        if self.test_mode_enabled():
            return first_page

        total_count = first_page["totalCount"]
        results = first_page["searchResults"]
        first_page_url = self.url

        for page in range(1, ceil(total_count / self.page_size)):
            self.url = self.build_url(page * self.page_size)
            page_results = (await super()._download(request_dict))[
                "searchResults"
            ]
            results.extend(page_results)

            if len(page_results) < self.page_size:
                # Last page of results; a further offset would 404
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

    def _process_html(self) -> None:
        """Parses HTML into case dictionaries

        :return: None
        """
        json = self.html
        for row in json["searchResults"]:
            fields = row["content"]["fields"]
            # `note` and `disposition` may come back as JSON null, in which
            # case `fields.get(..., "")` returns None instead of the default
            note = fields.get("note", "") or ""
            if note in ("Notice of Correction",):
                logger.info("Skipping non-opinion document %s", fields)
                continue

            name = fields.get("case_style", "")
            if not name:
                # These seem to be family - children related cases. See example
                # in district 4 example file
                # https://flcourts-media.ccplatform.net/content/download/2472477/28965542?version=5
                logger.info("Skipping case with no name %s", fields)
                continue

            disposition = fields.get("disposition", "") or ""
            self.cases.append(
                {
                    "url": urljoin(self.base_url, fields["opinion"]["uri"]),
                    "docket": self.get_docket_number(fields["case_number"]),
                    "name": titlecase(name),
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

        If no dates are passed, use the last `scrape_interval` days

        :param start: start date
        :param end: end date
        :return: none
        """
        if not start:
            end = datetime.today()
            start = end - timedelta(days=self.scrape_interval)

        self.start_date = start
        self.end_date = end
        self.url = self.build_url()

    def build_url(self, offset: int = 0) -> str:
        """Builds the URL of a single results page

        :param offset: index of the first result to return. The source 404s
            on offsets at or near the end of the results, so callers must keep
            it inside a page that `totalCount` covers
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

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Overrides scraper URL using date inputs

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.set_url(*dates)
        logger.info("Backscraping for range %s %s", *dates)
