"""
Scraper for the United States Bankruptcy Appellate Panel for the Tenth Circuit
CourtID: bap10
Court Short Name: 10th Cir. BAP
Auth: Jon Andersen <janderse@gmail.com>
Reviewer: mlr
History:
    2014-09-01: First draft by Jon Andersen
    2014-09-02: Revised by mlr to use _clean_text() instead of pushing logic
                into the _get_case_dates function.
"""

from datetime import date, datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = url = "https://www.bap10.uscourts.gov/opinion/search/results"
    first_opinion_date = datetime(1996, 11, 12)
    days_interval = 120

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.set_url()
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        for row in self.html.xpath(".//tr"):
            if not row.xpath(".//td"):
                continue
            self.cases.append(
                {
                    "docket": row.xpath(".//td")[0].text_content().strip(),
                    "name": row.xpath(".//td")[1].text_content().strip(),
                    "date": row.xpath(".//td")[2].text_content().strip(),
                    "url": row.xpath(".//a/@href")[0],
                    "status": "Published",
                }
            )

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        """Sets URL with date filters in query string

        :param start: optional start date
        :param end: optional end date
        :return None:
        """
        if not start:
            end = date.today()
            start = end - timedelta(30)

        params = {
            "keywords": "",
            "parties": "",
            "judges": "",
            "field_opinion_date_value[min][date]": start.strftime("%m/%d/%Y"),
            "field_opinion_date_value[max][date]": end.strftime("%m/%d/%Y"),
            "exclude": "",
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
