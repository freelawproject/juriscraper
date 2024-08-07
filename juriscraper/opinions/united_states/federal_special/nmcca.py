"""Scraper for the Navy-Marine Corps Court of Criminal Appeals
CourtID: nmcca
Court Short Name:
Reviewer: mlr
History:
    15 Sep 2014: Created by Jon Andersen
"""

from datetime import date, datetime
from typing import Tuple
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.jag.navy.mil/api/tables/decisions-opinions/data/"
    days_interval = 60
    first_opinion_date = datetime(2004, 1, 8)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.request["verify"] = False
        self.url = self.base_url
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        for row in self.html["results"]:
            date, docket, notes, name = list(row["data"].values())
            url = row["documents"][0]["document"]["download_url"]
            if notes == "Unpublished":
                status = "Unpublished"
            else:
                status = "Published"
            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "url": url,
                    "status": status,
                    "docket": docket,
                }
            )

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request

        "6e61b248-ef67-423e-b321-f2ed8ad05728" seems to be the name
        of the date field. It is also present on the response JSON keys.
        It seems stable through time, from last example file edit in 2023
        to April 2024.

        If something changes, go to
        https://www.jag.navy.mil/about/organization/ojag/code-05/nmcca/opinions/

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        ts = str(datetime.now().timestamp()).replace(".", "")[:13]
        start = dates[0].strftime("%Y-%m-%d")
        end = dates[1].strftime("%Y-%m-%d")
        params = {
            "page": "1",
            "page_size": "100",
            "ordering": "-data__6e61b248-ef67-423e-b321-f2ed8ad05728",
            "data__6e61b248-ef67-423e-b321-f2ed8ad05728__gte": start,
            "data__6e61b248-ef67-423e-b321-f2ed8ad05728__lte": end,
            "_": ts,
        }
        self.url = f"{self.base_url}?{urlencode(params)}"
        self.html = self._download()
        self._process_html()
