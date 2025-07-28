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
        self.url = f"https://www.asbca.mil/Decisions/decisions{self.year}.html"
        self.status = "Published"
        self.request["headers"] = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=0, i",
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        }
        self.needs_special_headers = True

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
