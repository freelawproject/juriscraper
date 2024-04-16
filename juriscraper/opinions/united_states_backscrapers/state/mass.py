import datetime
import re
from datetime import date, datetime
from typing import Any, Dict, Tuple

from dateutil import parser

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = datetime(1931, 2, 26)
    court_identifier = "SJC"
    # This mapper is incomplete
    backscrape_date_range_mapper = [
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.is_backscrape = False
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parse HTML into case dictionaries

        :return None
        """
        for row in self.html.xpath("//tr[td/a]"):
            _, date_filed_str, name = row.xpath("td/text()")
            date_filed = parser.parse(date_filed_str)
            if (
                self.start_date
                and self.start_date <= date_filed
                and date_filed <= self.end_date
            ):
                cite = row.xpath(".//a/text()")[0]
                url = row.xpath(".//a/@href")[0]
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

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Extracts docket number from downloaded opinion HTML

        Possible on SJC. since `Records And Briefs` section cites
            docket entries and each is labeled with the docket number
        Even when that sections does not exist, the docket number is available.
        For example: http://masscases.com/cases/sjc/493/493mass1019.html

        The format on App Ct opinions is different
        """
        if not self.is_backscrape:
            return {}
        match = re.search(rf"{self.court_identifier}-\d+", scraped_text[:2000])
        docket = match.group(0) if match else ""
        return {"Docket": {"docket_number": docket}}

    def _download_backwards(
        self, dates_and_url: Tuple[date, date, str]
    ) -> None:
        """Set proper `masscases.com` url as self.url, and parse content

        :param dates_and_url: contains target url, and start and end date used
            for filtering opinions of interest by date
        :return None
        """
        self.is_backscrape = True
        self.start_date, self.end_date, self.url = dates_and_url
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
        now = datetime.now()

        if start:
            start = datetime.strptime(start, "%m/%d/%Y")
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%m/%d/%Y")
        else:
            end = now

        assert start < end, "Incorrect backscraper start / end inputs"

        # If there is overlap between backscraping range and reports'
        # page range append the reports' page URL to the iterable
        self.back_scrape_iterable = []
        for item in self.backscrape_date_range_mapper:
            if max(item["start"], start) < min(item["end"] or now, end):
                self.back_scrape_iterable.append((start, end, item["url"]))
