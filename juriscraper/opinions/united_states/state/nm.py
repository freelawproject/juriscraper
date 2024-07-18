import datetime
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import make_date_range_tuples
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    """This site has an artificial limit of 50/1 minute and 100/5 minutes.

    To stay under that cap we are going to just request the first 10 opinions.  Judging on the number of opinions
    filed in each court we should be fine.

    Additionally, we moved docket number capture to PDF extraction, to limit the number of requests.
    """

    base_url = "https://nmonesource.com/nmos/en/d/s/index.do"
    court_code = "182"
    first_opinion_date = datetime(1900, 1, 1)
    days_interval = 15

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.set_url()
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parse HTML into case dictionaries

        XMLHttpRequest pagination is triggered every 25 rows, so we must
        try to avoid big date intervals

        :return None
        """
        rows = self.html.xpath("//div[@class='info']")
        if len(rows) >= 25:
            logger.info(
                "25 results for this query, results may be lost in pagination"
            )

        for row in rows:
            url = row.xpath(
                ".//a[contains(@title, 'Download the PDF version')]/@href"
            )[0]
            name = row.xpath(".//span[@class='title']/a/text()")[0]
            date_filed = row.xpath(".//span[@class='publicationDate']/text()")[
                0
            ]

            cite = row.xpath(".//span[@class='citation']/text()")
            citation = cite[0] if cite else ""

            status = "Unknown"
            metadata = row.xpath(".//div[@class='subMetadata']/span/text()")
            if metadata:
                status = (
                    "Published"
                    if "Reported" in metadata[-1]
                    else "Unpublished"
                )
            else:
                status = "Unknown"

            self.cases.append(
                {
                    "date": date_filed,
                    "docket": "",
                    "name": titlecase(name),
                    "citation": citation,
                    "url": url,
                    "status": status,
                }
            )

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        """Formats and sets `self.url` with date inputs

        If no start or end dates are given, scrape last 7 days.

        :param start: start date
        :param end: end date

        :return None
        """
        if not start:
            end = datetime.now() + timedelta(1)
            start = end - timedelta(7)

        params = {
            "cont": "",
            "ref": "",
            "d1": start.strftime("%m/%d/%Y"),
            "d2": end.strftime("%m/%d/%Y"),
            "col": self.court_code,
            "rdnpv": "",
            "rdnii": "",
            "rdnct": "",
            "ca": "",
            "p": "",
            "or": "date",
            "iframe": "true",
        }
        self.url = f"{self.base_url}?{urlencode(params)}"

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.set_url(*dates)
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.strptime(start, "%m/%d/%Y")
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%m/%d/%Y")
        else:
            end = datetime.now()

        self.back_scrape_iterable = make_date_range_tuples(
            start, end, self.days_interval
        )

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Pass scraped text into function and return data as a dictionary

        :param scraped_text: Text of scraped content
        :return: metadata
        """
        docket_number = re.findall(r"N[oO]\.\s(.*)", scraped_text)[0]
        metadata = {
            "OpinionCluster": {
                "docket_number": docket_number,
            },
        }
        return metadata
