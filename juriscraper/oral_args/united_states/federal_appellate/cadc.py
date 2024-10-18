"""Scraper for D.C. Circuit of Appeals
CourtID: cadc
Court Short Name: cadc
Author: Andrei Chelaru
Reviewer: mlr
Date created: 18 July 2014
Updated: 2024-10-10
"""

from datetime import date, datetime
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    days_interval = 28  # ensure monthly backscraper ticks
    first_opinion_date = datetime(2007, 9, 10)
    base_url = "https://media.cadc.uscourts.gov/recordings/bydate/{}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        self.url = self.base_url.format(today.strftime("%Y/%-m"))
        self.request["verify"] = False
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        anchor_xpath = "a[contains(@href, '/recordings/docs/') and contains(@href, '.mp3')]"
        for row in self.html.xpath(f"//div[div[div[div[{anchor_xpath}]]]]"):
            ahref = row.xpath(f".//{anchor_xpath}")
            url = ahref[0].xpath("@href")[0]
            docket = ahref[0].xpath("text()")[0]

            if "mp3" not in url:
                logger.info("Not a mp3 URL? %s", url)
                continue

            cells = row.xpath("div[2]/div")

            # From: "Judges: Tatel, Griffith, Sentelle"
            # To: "Tatel; Griffith; Sentelle"
            judges = (
                cells[1].text_content().split(": ", 1)[-1].replace(",", ";")
            )
            self.cases.append(
                {
                    "url": urljoin(self.base_url, url),
                    "docket": docket,
                    "name": cells[0].text_content(),
                    "judge": judges,
                    "attorney": cells[2].text_content(),
                    "date": cells[3].text_content(),
                }
            )

    def _download_backwards(self, target_date: date) -> None:
        """Download historical data

        Note that this URL will work:
        "https://media.cadc.uscourts.gov/recordings/bydate/2007/9"
        but this won't
        "https://media.cadc.uscourts.gov/recordings/bydate/2007/09"

        That's why the '%-m' formatter is needed
        """
        self.url = self.base_url.format(target_date.strftime("%Y/%-m"))
        logger.info("Backscraping URL '%s'", self.url)
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Use base function to generate a range, then pick
        unique year-month combinations to build the backscrape
        URLS
        """
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )
