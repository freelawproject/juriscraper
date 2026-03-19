"""
Scraper for Kansas Supreme Court
CourtID: kan
Court Short Name: Kansas
Author: William Palin
Court Contact:
History:
 - 2025-06-09: Created.
 - 2026-03-19: Refactored from WebDriven to OpinionSiteLinear. grossir
    Use urllib to fix block
    Added backscraper
"""

import urllib.request
from datetime import date, timedelta
from urllib.parse import urlencode, urljoin

from lxml.html import fromstring

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://searchdro.kscourts.gov"
    court_string = "Supreme Court"
    court_filter = "10"
    first_opinion_date = date(2015, 1, 1)
    days_interval = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        self.url = self._make_search_url(today - timedelta(days=30), today)
        self.make_backscrape_iterable(kwargs)

    def _make_search_url(self, start: date, end: date) -> str:
        params = {
            "StartDate": start.strftime("%Y-%m-%d"),
            "EndDate": end.strftime("%Y-%m-%d"),
            "statusFilter": "-1",
            "courtFilter": self.court_filter,
            "Keyword": "",
        }
        return urljoin(self.base_url, f"/Documents/Search?{urlencode(params)}")

    def _fetch_url(self, url: str):
        """Fetch a URL using urllib to bypass Cloudflare's TLS
        fingerprinting. httpx gets 403'd due to its TLS fingerprint
        (httpcore). Python's stdlib urllib uses a different TLS stack
        that Cloudflare does not block.

        :param url: URL to fetch
        :return: response content (not decoded)
        """
        req = urllib.request.Request(
            url,
            headers={"User-Agent": self.user_agent},
        )
        response = urllib.request.urlopen(req)
        response_content = response.read()
        self.do_save_response(response, response_content)

        return response_content

    def do_save_response(self, response, response_content: bytes) -> None:
        """Call `save_response` over non standard urllib responses

        Prepare urllib (not standard) response objects to
        behave have httpx / requests response attributes

        This must work both with `sample_caller` and
        Courtlistener's save_response (that saves to S3)

        :param response: a urllib response
        :param response_content: bytes of the response
        :return None
        """
        self.request["response"] = response

        if not self.save_response:
            return

        response.text = response_content.decode("utf-8")
        response.content = response_content
        response.history = []
        self.save_response(self)

    async def _download(self, request_dict=None):
        if self.test_mode_enabled():
            with open(self.mock_url, mode="rb") as f:
                response_text = f.read().decode("utf-8")
        else:
            response_content = self._fetch_url(self.url)
            response_text = response_content.decode("utf-8")
        self.html = fromstring(response_text)
        return self.html

    def _process_html(self):
        """Parse the /Documents/Search results table.

        Columns: Release Date, Case Number, Case Title, Court, Status, PDF
        """

        for row in self.html.xpath("//table//tr[not(.//th)]"):
            cells = row.xpath(".//td")
            if len(cells) < 6:
                logger.warning("Skipping malformed row %s", cells)
                continue

            court = cells[3].text_content().strip()
            if court != self.court_string:
                logger.warning("Skipping record from other court, %s", cells)
                continue

            url = cells[5].xpath(".//a/@href")
            self.cases.append(
                {
                    "date": cells[0].text_content().strip(),
                    "docket": cells[1].text_content().strip(),
                    "name": cells[2].text_content().strip(),
                    "status": cells[4].text_content().strip(),
                    "url": urljoin(self.base_url, url[0]),
                }
            )

    async def _download_backwards(self, dates: tuple) -> None:
        """Backscrape using the /Documents/Search endpoint

        :param dates: (start_date, end_date) tuple
        :return: None
        """
        start, end = dates
        logger.info("Backscraping for date range %s %s", start, end)
        self.url = self._make_search_url(start, end)
        self.html = await self._download()
        self._process_html()
