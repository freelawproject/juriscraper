import re
from datetime import datetime
from typing import TypedDict

from dateutil import parser
from lxml.html import HtmlElement, fromstring
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, clean_string
from juriscraper.lib.type_utils import BackscrapeOptions, ExtractedMetadata
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class _BackscrapeDateRange(TypedDict):
    start: datetime
    end: datetime | None
    url: str


class Site(OpinionSiteLinear[tuple[datetime, datetime, str]]):
    start_date: datetime
    end_date: datetime

    first_opinion_date = datetime(1931, 2, 26)
    docket_number_regex = r"SJC-\d+"
    # This mapper is missing older volumes
    backscrape_date_range_mapper: list[_BackscrapeDateRange] = [
        {
            "start": datetime(2016, 7, 25),
            "end": None,
            "url": "http://masscases.com/475-499.html",
        },
        {
            "start": datetime(2007, 10, 25),
            "end": datetime(2016, 5, 26),
            "url": "http://masscases.com/450-474.html",
        },
        {
            "start": datetime(1997, 5, 15),
            "end": datetime(2007, 9, 28),
            "url": "http://masscases.com/425-449.html",
        },
        {
            "start": datetime(1987, 5, 14),
            "end": datetime(1997, 5, 12),
            "url": "http://masscases.com/400-424.html",
        },
        {
            "start": datetime(1931, 2, 25),
            "end": datetime(1938, 3, 8),
            "url": "http://masscases.com/275-299.html",
        },
    ]
    # on the cl_scrape_opinions command in Courtlistener,
    # a headers variable is required for mass
    headers: dict[str, str] = {}

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[datetime, datetime, str]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.make_backscrape_iterable(kwargs)
        self.expected_content_types = ["text/html"]

    @override
    def _process_html(self) -> None:
        """Parse HTML into case dictionaries

        :return None
        """
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//tr[td/a]")
        for row in rows:
            texts: list[str] = row.xpath("td/text()")
            _, date_filed_str, *name = texts
            # Edge case where date is a range "December 8, 2000 - January 3, 2001"
            date_filed_str = date_filed_str.partition(" - ")[0]
            date_filed = parser.parse(date_filed_str)

            if not (
                bool(self.start_date)
                and self.start_date <= date_filed
                and date_filed <= self.end_date
            ):
                continue

            # Consolidated cases, for example 432 Mass. 489
            # on year 2000
            name = "; ".join(name).strip()
            cite: str = row.xpath(".//a/text()")[0]
            url: str = row.xpath(".//a/@href")[0]
            self.cases.append(
                {
                    "citation": cite,
                    "date": date_filed_str,
                    "name": name,
                    "url": url,
                    "docket": "",
                    "status": "Published",
                }
            )

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extracts docket number from downloaded opinion HTML

        Possible on SJC. since `Records And Briefs` section cites
            docket entries and each is labeled with the docket number
        Even when that sections does not exist, the docket number is available
        in the headnotes section
        For example: http://masscases.com/cases/sjc/493/493mass1019.html

        The format on App Ct opinions is different
        """
        match = re.search(self.docket_number_regex, scraped_text[:2000])
        docket = match.group(0) if match is not None else ""

        headnotes, summary = "", ""
        html = fromstring(scraped_text)
        headnote_section: list[HtmlElement] = html.xpath(
            "//section[@class='headnote']"
        )
        synopsis_section: list[HtmlElement] = html.xpath(
            "//section[@class='synopsis']"
        )

        if bool(headnote_section):
            # First line of the headnote might be the docket number
            headnotes = clean_string(
                headnote_section[0].text_content().replace(docket, "")
            )
        if bool(synopsis_section):
            paragraphs: list[HtmlElement] = synopsis_section[0].xpath(
                ".//p[not(@class)]"
            )
            summary = "\n".join(
                [
                    clean_string(p.text_content())
                    # avoid page numbers
                    for p in paragraphs
                ]
            )

        return {
            "Docket": {"docket_number": docket},
            "OpinionCluster": {"headnotes": headnotes, "summary": summary},
        }

    @override
    async def _download_backwards(
        self, dates_and_url: tuple[datetime, datetime, str]
    ) -> None:
        """Set proper `masscases.com` url as self.url, and parse content

        :param dates_and_url: contains target url, and start and end date used
            for filtering opinions of interest by date
        :return None
        """
        self.start_date, self.end_date, self.url = dates_and_url
        self.html = await self._download()
        self._process_html()

    @override
    def make_backscrape_iterable(self, kwargs: BackscrapeOptions) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly
        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")
        now = datetime.now()

        if bool(start):
            start = datetime.strptime(start, "%m/%d/%Y")
        else:
            start = self.first_opinion_date
        if bool(end):
            end = datetime.strptime(end, "%m/%d/%Y")
        else:
            end = now

        if start >= end:
            raise ValueError("Incorrect backscraper start / end inputs")

        # If there is overlap between backscraping range and reports'
        # page range append the reports' page URL to the iterable
        self.back_scrape_iterable = []
        for item in self.backscrape_date_range_mapper:
            if max(item["start"], start) < min(
                (item["end"] if item["end"] is not None else now), end
            ):
                self.back_scrape_iterable.append((start, end, item["url"]))
