# Court Contact: bkraft@courts.ms.gov (see https://courts.ms.gov/aoc/aoc.php)

import datetime
from collections.abc import Mapping
from posixpath import normpath
from typing import NotRequired
from urllib.parse import urljoin, urlparse, urlunparse

from lxml import html
from lxml.html import HtmlElement
from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import RequestParameters, SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker, convert_date_string
from juriscraper.lib.type_utils import BackscrapeOptions
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class _DatesResponse(TypedDict):
    dates: NotRequired[str | None]


_dates_adapter = TypeAdapter(_DatesResponse)


# Landing page: https://courts.ms.gov/appellatecourts/sc/scdecisions.php
class Site(OpinionSiteLinear[tuple[int, datetime.date, datetime.date]]):
    court_parameter = "SCT"
    domain = "https://courts.ms.gov"
    first_opinion_year = 1996

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[
            SiteOptions[tuple[int, datetime.date, datetime.date]]
        ],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.method = "POST"
        self.url = f"{self.domain}/appellatecourts/docket/getHanddown.php"

        self.needs_special_headers = True
        self.parameters = {
            "court": self.court_parameter,
            "year": str(datetime.date.today().year),
        }
        # The site's WAF answers 500 with a "Website Maintenance" page to
        # user agents on its bot list, which includes "Juriscraper" and
        # outdated browser versions, so `AbstractSite.chrome_version` needs
        # to be bumped when the court starts failing again. See #2129
        self.request["headers"]["User-Agent"] = self.chrome_user_agent

        self.status = "Published"
        self.pages: dict[str, HtmlElement] = {}

        # Date filter: regular scraper checks last 15 days;
        # backscraper overrides these in _download_backwards
        today = datetime.date.today()
        self.start_date = today - datetime.timedelta(days=15)
        self.end_date = today

        self.make_backscrape_iterable(kwargs)

    @override
    async def _download(
        self, request_dict: RequestParameters | None = None
    ) -> None:
        """Fetch hand-down dates from the API, filter to the date
        range, and download each date's opinion list page.
        """
        self.pages = {}

        if self.test_mode_enabled():
            # Example files are individual date pages
            tree = await super()._download(request_dict)
            if not isinstance(tree, HtmlElement):
                raise TypeError("Expected a downloaded HTML document")
            self.pages["2020-02-28"] = tree
            return

        self._process_request_parameters(request_dict)
        self.downloader_executed = True
        if self.url is None:
            raise ValueError("The hand-down API URL is not configured")
        await self._request_url_post(self.url)
        self._post_process_response()
        response = self.request.get("response")
        if response is None:
            raise ValueError("Download a response before accessing it.")
        dates_response: object = response.json()

        all_dates = self.get_dates_from_response(dates_response)
        for date in all_dates:
            if not (self.start_date <= date <= self.end_date):
                logger.info("Skipping date out of range %s", date)
                continue

            date_str = datetime.date.strftime(date, "%m-%d-%Y")
            path = f"/Images/HDList/{self.court_parameter}{date_str}.html"
            url = urljoin(self.domain, path)

            logger.info("Getting opinion list at %s", url)
            page = await self._get_html_tree_by_url(url)
            self.pages[f"{date}"] = page

    def get_dates_from_response(
        self, dates_response: object
    ) -> list[datetime.date]:
        """Extract all available dates from the API JSON response.

        Response contains an HTML select element in the "dates" field:
        {"dates": "<select ...><option value='01-08-2026'>...</option>..."}
        """
        dates: list[datetime.date] = []
        dates_html = _dates_adapter.validate_python(
            dates_response, strict=True
        ).get("dates", "")
        if not bool(dates_html):
            logger.warning(
                "%s: No 'dates' in API response for %s/%s",
                self.court_id,
                self.court_parameter,
                self.parameters.get("year")
                if isinstance(self.parameters, Mapping)
                else "",
            )
            return dates

        tree = html.fromstring(dates_html)
        values: list[str] = tree.xpath("//option/@value")
        for value in values:
            try:
                parsed = convert_date_string(value)
                if parsed is None:
                    raise ValueError("Empty hand-down date")
                dates.append(parsed)
            except ValueError:
                logger.warning(
                    "%s: Could not parse date value '%s'",
                    self.court_id,
                    value,
                )
        dates.sort(reverse=True)
        return dates

    @override
    def _process_html(self) -> None:
        for date, page in self.pages.items():
            anchors: list[HtmlElement] = page.xpath(
                ".//a[contains(./@href, '.pdf')]"
            )
            for anchor in anchors:
                # Walk up to the containing <td> (table layout)
                # or to body's direct child (flat layout)
                parent = anchor.getparent()
                if parent is None:
                    continue
                while (grandparent := parent.getparent()) is not None:
                    if parent.tag == "td" or grandparent.tag == "body":
                        break
                    parent = grandparent

                # Table layout: <ul> is a descendant of the <td>
                # Flat layout: <ul> is a following sibling
                if parent.tag == "td":
                    sections = parent.findall(".//ul")
                else:
                    sections: list[HtmlElement] = parent.xpath(
                        "./following-sibling::ul"
                    )

                if not bool(sections):
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
                raw_url: str = anchor.xpath("./@href")[0]
                raw_url = raw_url.replace("\\", "/")
                parsed = urlparse(raw_url)
                url = urlunparse(parsed._replace(path=normpath(parsed.path)))
                self.cases.append(
                    {
                        "date": date,
                        "docket": anchor.text_content().strip(),
                        "name": section.findall(".//b")[0]
                        .text_content()
                        .strip(),
                        "summary": section.text_content().strip(),
                        "url": url,
                    }
                )

    @override
    def make_backscrape_iterable(self, kwargs: BackscrapeOptions) -> None:
        """The API only filters by year. We iterate by year but
        filter available dates to the backscrape date range, to
        minimize requests to the court's server.

        Accepts backscrape_start/end in "%Y/%m/%d" format.
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if bool(start):
            start = datetime.datetime.strptime(start, "%Y/%m/%d").date()
        else:
            start = datetime.date(self.first_opinion_year, 1, 1)

        if bool(end):
            end = datetime.datetime.strptime(end, "%Y/%m/%d").date()
        else:
            end = datetime.date.today()

        self.back_scrape_iterable = [
            (year, start, end) for year in range(start.year, end.year + 1)
        ]

    @override
    async def _download_backwards(
        self, params: tuple[int, datetime.date, datetime.date]
    ) -> None:
        year, start, end = params
        logger.info("Backscraping %s for year %s", self.court_id, year)

        # reset so each backscraper tick has a fresh list
        self.pages = {}

        if not isinstance(self.parameters, dict):
            raise TypeError("Search parameters must be a dictionary.")
        self.parameters["year"] = str(year)
        self.start_date = start
        self.end_date = end

        await self._download()
        self._process_html()
