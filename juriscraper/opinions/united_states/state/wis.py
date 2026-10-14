import re
from datetime import date, datetime, timedelta
from urllib.parse import urlencode, urljoin

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import ExtractedMetadata
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[tuple[date, date]]):
    days_interval = 15
    first_opinion_date = datetime(1995, 6, 1).date()

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.wicourts.gov/supreme/scopin.jsp"
        self.status = "Published"
        self.set_url()
        self.cite_regex = r"20\d{2}\sWI\s\d+"
        self.make_backscrape_iterable(kwargs)

    def set_url(
        self, start: date | None = None, end: date | None = None
    ) -> None:
        """Sets URL with appropriate query parameters

        :param start: start date
        :param end: end date
        :return None
        """
        if end is None:
            end = datetime.today()
        if start is None:
            start = end - timedelta(days=15)

        params = {
            "range": "None",
            "begin_date": start.strftime("%m-%d-%Y"),
            "end_date": end.strftime("%m-%d-%Y"),
            "sortBy": "date",
            "Submit": "Search",
        }
        self.url = f"{self.base_url}?{urlencode(params)}"

    @override
    def _process_html(self) -> None:
        """Process the HTML from wisconsin

        :return: None
        """
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(".//table/tbody/tr")
        for row in rows:
            date, docket, caption, link = row.findall("./td")
            self.cases.append(
                {
                    "date": date.text,
                    "name": caption.text_content(),
                    "url": urljoin(
                        "https://www.wicourts.gov",
                        link.findall("./input")[0].attrib["name"],
                    ),
                    "docket": docket.text,
                }
            )

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract citation from text

        :param scraped_text: Text of scraped content
        :return: date filed
        """
        first_line = scraped_text[:100].splitlines()[0]
        if (match := re.search(self.cite_regex, first_line)) is not None:
            return {"Citation": match.group(0)}

        return {}

    @override
    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Set date range from backscraping args and scrape

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.set_url(*dates)
        self.html = await self._download()
        self._process_html()
