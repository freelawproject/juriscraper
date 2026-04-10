# Court Contact: bkraft@courts.ms.gov (see https://courts.ms.gov/aoc/aoc.php)

import datetime
from posixpath import normpath
from urllib.parse import urljoin, urlparse, urlunparse

from lxml import html

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


# Landing page: https://courts.ms.gov/appellatecourts/sc/scdecisions.php
class Site(OpinionSiteLinear):
    court_parameter = "SCT"
    domain = "https://courts.ms.gov"
    first_opinion_year = 1996

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.method = "POST"
        self.url = f"{self.domain}/appellatecourts/docket/getHanddown.php"

        self.needs_special_headers = True
        self.parameters = {
            "court": self.court_parameter,
            "year": str(datetime.date.today().year),
        }
        self.request["headers"]["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        self.status = "Published"
        self.pages = {}

        # Date filter: regular scraper checks last 15 days;
        # backscraper overrides these in _download_backwards
        today = datetime.date.today()
        self.start_date = today - datetime.timedelta(days=15)
        self.end_date = today

        self.make_backscrape_iterable(kwargs)

    async def _download(self, request_dict=None):
        """Fetch hand-down dates from the API, filter to the date
        range, and download each date's opinion list page.
        """
        self.pages = {}

        if self.test_mode_enabled():
            # Example files are individual date pages
            self.pages["2020-02-28"] = await super()._download(request_dict)
            return

        self._process_request_parameters(request_dict)
        self.downloader_executed = True
        await self._request_url_post(self.url)
        self._post_process_response()
        dates_response = self.request["response"].json()

        all_dates = self.get_dates_from_response(dates_response)
        for date in all_dates:
            if not (self.start_date <= date <= self.end_date):
                logger.info("Skipping date out of range")
                continue

            date_str = datetime.date.strftime(date, "%m-%d-%Y")
            path = f"/Images/HDList/{self.court_parameter}{date_str}.html"
            url = urljoin(self.domain, path)

            logger.info("Getting opinion list at %s", url)
            page = await self._get_html_tree_by_url(url)
            self.pages[f"{date}"] = page

    def get_dates_from_response(self, dates_response):
        """Extract all available dates from the API JSON response.

        Response contains an HTML select element in the "dates" field:
        {"dates": "<select ...><option value='01-08-2026'>...</option>..."}
        """
        dates = []
        dates_html = dates_response.get("dates", "")
        if not dates_html:
            logger.warning(
                "%s: No 'dates' in API response for %s/%s",
                self.court_id,
                self.court_parameter,
                self.parameters.get("year"),
            )
            return dates

        tree = html.fromstring(dates_html)
        for value in tree.xpath("//option/@value"):
            try:
                dates.append(convert_date_string(value))
            except ValueError:
                logger.warning(
                    "%s: Could not parse date value '%s'",
                    self.court_id,
                    value,
                )
        dates.sort(reverse=True)
        return dates

    def _process_html(self):
        for date, page in self.pages.items():
            for anchor in page.xpath(".//a[contains(./@href, '.pdf')]"):
                # Walk up to the containing <td> (table layout)
                # or to body's direct child (flat layout)
                parent = anchor.getparent()
                while parent.getparent() is not None:
                    if parent.tag == "td" or parent.getparent().tag == "body":
                        break
                    parent = parent.getparent()

                # Table layout: <ul> is a descendant of the <td>
                # Flat layout: <ul> is a following sibling
                if parent.tag == "td":
                    sections = parent.xpath(".//ul")
                else:
                    sections = parent.xpath("./following-sibling::ul")

                if not sections:
                    docket = anchor.text_content().strip()
                    logger.warning(
                        "%s: No case details <ul> found for docket %s on %s",
                        self.court_id,
                        docket,
                        date,
                    )
                    continue

                section = sections[0]
                # Raw hrefs use backslashes (e.g. "..\Opinions\file.pdf")
                # which make_links_absolute doesn't normalize.
                # Replace backslashes and resolve the ".." path segments.
                raw_url = anchor.xpath("./@href")[0].replace("\\", "/")
                parsed = urlparse(raw_url)
                url = urlunparse(parsed._replace(path=normpath(parsed.path)))
                self.cases.append(
                    {
                        "date": date,
                        "docket": anchor.text_content().strip(),
                        "name": section.xpath(".//b")[0]
                        .text_content()
                        .strip(),
                        "summary": section.text_content().strip(),
                        "url": url,
                    }
                )

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """The API only filters by year. We iterate by year but
        filter available dates to the backscrape date range, to
        minimize requests to the court's server.

        Accepts backscrape_start/end in "%Y/%m/%d" format.
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.datetime.strptime(start, "%Y/%m/%d").date()
        else:
            start = datetime.date(self.first_opinion_year, 1, 1)

        if end:
            end = datetime.datetime.strptime(end, "%Y/%m/%d").date()
        else:
            end = datetime.date.today()

        self.back_scrape_iterable = [
            (year, start, end) for year in range(start.year, end.year + 1)
        ]

    async def _download_backwards(self, params: tuple) -> None:
        year, start, end = params
        logger.info("Backscraping %s for year %s", self.court_id, year)

        # reset so each backscraper tick has a fresh list
        self.pages = {}

        self.parameters["year"] = str(year)
        self.start_date = start
        self.end_date = end

        await self._download()
        self._process_html()
