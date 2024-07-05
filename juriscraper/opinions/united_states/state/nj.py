import re
from datetime import date, datetime
from typing import Tuple
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import make_date_range_tuples
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = datetime(2013, 1, 14)
    days_interval = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = self.url = (
            "https://www.njcourts.gov/attorneys/opinions/supreme"
        )
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        for row in self.html.xpath("//div[@class='card-body']"):
            container = row.xpath(".//a[@class='text-underline-hover']")
            if not container:
                logger.warning(
                    "Skipping row with no URL: %s",
                    re.sub(r"\s+", " ", row.text_content()),
                )
                continue

            url = container[0].xpath("@href")[0]
            # name is sometimes inside a span, not inside the a tag
            name_content = container[0].xpath("string(.)")
            name_str, _, _ = name_content.partition("(")

            docket = row.xpath('.//*[contains(@class, "mt-1")]/text()')[
                0
            ].strip()
            date = row.xpath(
                ".//div[@class='col-lg-12 small text-muted mt-2']/text()"
            )[0]

            case = {
                "date": date,
                "docket": docket,
                "name": titlecase(name_str.strip()),
                "url": url,
            }

            if self.status == "Published":
                summary = row.xpath(".//div[@class='modal-body']/p/text()")
                case["summary"] = "\n".join(summary)

            self.cases.append(case)

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

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        params = {
            "start": dates[0].strftime("%Y-%m-%d"),
            "end": dates[1].strftime("%Y-%m-%d"),
        }
        self.url = f"{self.base_url}?{urlencode(params)}"
        self.html = self._download()
        self._process_html()
