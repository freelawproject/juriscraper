import re
from datetime import date, datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import urlencode, urljoin

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    days_interval = 15
    first_opinion_date = datetime(1995, 6, 1).date()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.wicourts.gov/supreme/scopin.jsp"
        self.status = "Published"
        self.set_url()
        self.cite_regex = r"20\d{2}\sWI\s\d+"
        self.make_backscrape_iterable(kwargs)

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        """Sets URL with appropriate query parameters

        :param start: start date
        :param end: end date
        :return None
        """
        if not start:
            start = datetime.today() - timedelta(days=15)
            end = datetime.today()

        start = start.strftime("%m-%d-%Y")
        end = end.strftime("%m-%d-%Y")

        params = {
            "range": "None",
            "begin_date": start,
            "end_date": end,
            "sortBy": "date",
            "Submit": "Search",
        }
        self.url = f"{self.base_url}?{urlencode(params)}"

    def _process_html(self) -> None:
        """Process the HTML from wisconsin

        :return: None
        """
        for row in self.html.xpath(".//table/tbody/tr"):
            date, docket, caption, link = row.xpath("./td")
            self.cases.append(
                {
                    "date": date.text,
                    "name": caption.text,
                    "url": urljoin(
                        "https://www.wicourts.gov",
                        link.xpath("./input")[0].name,
                    ),
                    "docket": docket.text,
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract citation from text

        :param scraped_text: Text of scraped content
        :return: date filed
        """
        first_line = scraped_text[:100].splitlines()[0]
        if match := re.search(self.cite_regex, first_line):
            return {"Citation": match.group(0)}

        return {}

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Set date range from backscraping args and scrape

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.set_url(*dates)
        self.html = self._download()
        self._process_html()
