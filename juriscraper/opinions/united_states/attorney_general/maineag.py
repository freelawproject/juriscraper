"""
Scraper for Maine Attorney General
CourtID: paag
Court Short Name: Maine AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
import re
from datetime import datetime as dt

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://www.maine.gov/ag/about/ag_opinions.html"
        self.year = dt.today().year

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//li/a[contains(@href, '.pdf')]"):
            date, name = row.xpath(".//text()")[0].split(" ", 1)
            self.cases.append(
                {
                    "url": row.xpath(".//@href")[0],
                    "docket": "",
                    "name": name.split("(PDF")[0],
                    "date": date,
                }
            )
