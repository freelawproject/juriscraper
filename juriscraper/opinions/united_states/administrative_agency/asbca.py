"""Scraper for Armed Services Board of Contract Appeals
CourtID: asbca
Court Short Name: ASBCA
Author: Jon Andersen
Reviewer: mlr
History:
    2014-09-11: Created by Jon Andersen
    2016-03-17: Website and phone are dead. Scraper disabled in __init__.py.
"""

from datetime import datetime

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = str(datetime.today().year)
        self.url = f"http://www.asbca.mil/Decisions/decisions{self.year}.html"
        self.status = "Published"

    def _process_html(self):
        # Exclude headers and rows that only have the month name
        if self.test_mode_enabled():
            self.year = "2024"

        rows = self.html.xpath(
            "//tr[not(th) and not(.//span[@style='background-color:#F8C100;'])]"
        )
        for row in rows:
            if len(row.xpath(".//td")) != 4:
                logger.warning(
                    "Row does not have expected number of cells %s",
                    row.text_content().strip(),
                )
                continue

            url = row.xpath(".//a/@href")
            url = url[0]
            date, docket, name, judge = (
                cell.text_content().strip() for cell in row.xpath(".//td")
            )

            if self.year not in date:
                # site returns all records in a single request
                # in a normal scrape, check only the most recent year
                break

            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "url": url,
                    "docket": docket,
                    "judge": judge,
                }
            )
