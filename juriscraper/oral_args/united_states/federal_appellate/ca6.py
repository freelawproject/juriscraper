"""Oral Argument Audio Scraper for Court of Appeals for the Sixth Circuit
CourtID: ca6
Court Short Name: 6th Cir.
Court Contact: WebSupport@ca6.uscourts.gov
Authors: Brian W. Carver, Michael Lissner
Reviewer: None
History:
  2014-11-06: Started by Brian W. Carver and wrapped up by mlr.
  2016-06-30: Updated by mlr.
  2025-01-21: Updated to OralArgumentSiteLinear by grossir
"""

import re
from datetime import date, datetime

from juriscraper.AbstractSite import logger
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    days_interval = 10000  # force a single interval
    first_opinion_date = datetime(2012, 12, 1)
    # check the first 100 records; Otherwise, it will try to download more
    # than 1000 every time
    limit = 100

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.opn.ca6.uscourts.gov/internet/court_audio/aud1.php"
        )
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """All parsable fields are contained in the URL

        Parsing the URL helps simplifying the backscraper which has a different
        HTML structure than the regular page
        """
        for link in self.html.xpath("//a[text()='Play']/@href")[: self.limit]:
            *_, date_str, case = link.split("/")
            docket_match = re.search(r"(\d{2}-\d{4}\s?)+", case)
            if not docket_match:
                logger.warning("Skipping row %s", link)
                continue

            docket = docket_match.group(0).strip()
            name = case[docket_match.end() : case.find(".mp3")].strip()
            self.cases.append(
                {
                    "docket": docket,
                    "name": name,
                    "url": link,
                    "date": date_str.rsplit("-", 1)[0].strip(),
                }
            )

    def _download_backwards(self, dates: tuple[date]) -> None:
        """Downloads and parses older records according to input dates"""
        logger.info("Backscraping for range %s", *dates)
        self.limit = 10000  # disable limit
        self.method = "POST"
        self.url = "https://www.opn.ca6.uscourts.gov/internet/court_audio/audSearchRes.php"
        self.parameters = {
            "caseNumber": "",
            "shortTitle": "",
            "dateFrom": dates[0].strftime("%m/%d/%y"),
            "dateTo": dates[1].strftime("%m/%d/%y"),
            "Submit": "Submit+Query",
        }
        self.html = self._download()
        self._process_html()
