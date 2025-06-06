"""
CourtID: kan_p
Court Short Name: Kansas Supreme Court (published)
History:
    2025-06-05, quevon24: Implemented new site
"""

import re
from datetime import date, datetime
from typing import Optional
from urllib.parse import urlencode

from dateutil.relativedelta import relativedelta

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_filter = 10  # Supreme Court
    status_filter = 1  # Published
    days_interval = 7
    first_opinion_date = datetime(2016, 1, 22)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://searchdro.kscourts.gov/Documents/Search"
        self.set_url()
        self.make_backscrape_iterable(kwargs)

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        """Sets URL with date filters in query string

        :param start: optional start date
        :param end: optional end date
        :return None:
        """

        if not start:
            start = date.today() - relativedelta(months=1)
            end = date.today()

        params = {
            "statusFilter": self.status_filter,
            "startDate": start.strftime("%Y-%m-%d"),
            "endDate": end.strftime("%Y-%m-%d"),
            "courtFilter": self.court_filter,
        }
        self.url = f"{self.base_url}?{urlencode(params)}"

    def _process_html(self):
        for row in self.html.xpath(
            '//table[@id="searchResultsTable"]//tbody/tr'
        ):
            date_filed, docket_number, case_name, court, status = row.xpath(
                ".//td/text()"
            )

            cleaned_case_name = re.sub(r"\s+", " ", case_name).strip()

            url = row.xpath(".//td/a")[0].get("href")
            self.cases.append(
                {
                    "status": status,
                    "date": date_filed,
                    "docket": docket_number,
                    "name": cleaned_case_name,
                    "url": url,
                }
            )

    def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Build URL with year input and scrape

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.set_url(start=dates[0], end=dates[1])
        self.html = self._download()
        self._process_html()
