# Scraper for Florida Supreme Court
# CourtID: fla
# Court Short Name: fla

from datetime import date, datetime, timedelta
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # The source exposes no publication time. `publish_date` is null on every
    # district court row, `modified` moves whenever the CMS touches a record,
    # and `content.id` is a bulk creation sequence that tracks the case
    # number. So there is no key that puts newly posted opinions above ones
    # already ingested, and CourtListener has to walk the whole list. #2152
    is_recency_ordered = False
    days_interval = 20
    first_opinion_date = datetime(1999, 9, 23)
    # The source caps a page at 50 results, whatever `limit` asks for
    page_size = 50
    # A `totalCount` the source cannot deliver must not spin forever
    max_pages = 20
    # A regular scrape only needs to cover a scraper outage. The old 365 day
    # window was meaningless anyway: it always returned the newest page and
    # dropped the rest. #2150
    lookback_days = 15
    base_url = "https://flcourts-media.flcourts.gov/_search/opinions/?limit={}&offset={}&query=&scopes[]={}&searchtype=opinions&siteaccess={}&startdate={}&enddate={}"
    scopes = "supreme_court"
    site_access = "supreme2"
    # Example built URL
    # "https://flcourts-media.flcourts.gov/_search/opinions/?startdate=2025-07-01&limit=50&offset=0&query=&scopes[]=supreme_court&searchtype=opinions&siteaccess=supreme2&enddate=2026-01-01"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.start_date = None
        self.end_date = None
        self.set_url()
        self.make_backscrape_iterable(kwargs)

    async def _download(self, request_dict=None):
        """Download every page of the result set

        The source caps a page at 50 results and reports the size of the whole
        set in `totalCount`, so anything past the first page needs another
        request. Without this, a day with more than 50 opinions silently loses
        its tail, and a busy backscrape window loses about half of it. #2150

        :param request_dict: passed through to the base downloader
        :return: the first page, holding the results of every page
        """
        response = await super()._download(request_dict)
        if self.test_mode_enabled():
            return response

        results = response["searchResults"]
        total = response.get("totalCount", len(results))

        pages = 1
        while len(results) < total:
            if pages >= self.max_pages:
                logger.error(
                    "%s: stopped after %s pages holding %s of %s results. "
                    "The rest of this window was not scraped",
                    self.court_id,
                    pages,
                    len(results),
                    total,
                )
                break

            self.set_url(self.start_date, self.end_date, offset=len(results))
            page = await super()._download(request_dict)
            page_results = page["searchResults"]
            if not page_results:
                logger.error(
                    "%s: the page at offset %s came back empty, holding %s "
                    "of %s results. The rest was not scraped",
                    self.court_id,
                    len(results),
                    len(results),
                    total,
                )
                break

            results.extend(page_results)
            pages += 1

        # leave `self.url` describing the query, not the last offset fetched
        self.set_url(self.start_date, self.end_date)
        return response

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
        self,
        start: date | None = None,
        end: date | None = None,
        offset: int = 0,
    ) -> None:
        """Sets URL using date arguments

        If no dates are passed, cover the last `lookback_days`. The window is
        kept on the instance so `_download` can ask for further pages of the
        same query.

        :param start: start date
        :param end: end date
        :param offset: how many results to skip, for pagination
        :return: none
        """
        if not start:
            end = datetime.today()
            start = end - timedelta(days=self.lookback_days)

        self.start_date = start
        self.end_date = end

        fmt = "%Y-%m-%d"
        self.url = self.base_url.format(
            self.page_size,
            offset,
            self.scopes,
            self.site_access,
            start.strftime(fmt),
            end.strftime(fmt),
        )

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Overrides scraper URL using date inputs

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.set_url(*dates)
        logger.info("Backscraping for range %s %s", *dates)
