"""Scraper for D.C. Circuit of Appeals
CourtID: cadc
Court Short Name: cadc
Author: Andrei Chelaru
Reviewer: mlr
Date created: 18 July 2014

Updated: 2024-10-10
"""

from datetime import date

from juriscraper.AbstractSite import logger
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    days_interval = 28

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.d = date.today()
        self.url = "https://media.cadc.uscourts.gov/recordings/bydate/{yearmo}".format(
            yearmo=self.d.strftime("%Y/%m")
        )
        self.parameters = {"verify": False}
        # self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        """"""
        for row in self.html.xpath(".//div[@class='mt-0 pt-0 pb-3 row']"):
            ahref = row.xpath(".//div/div/a")
            url = ahref[0].xpath(".//@href")[0]
            docket = ahref[0].xpath(".//text()")[0]
            if "mp3" not in url:
                logger.info("Audio likely missing")
                continue
            cells = row.xpath(".//div[@class='col-sm-9 ml-3 ml-sm-0']/div")

            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": cells[0].text_content(),
                    "date": cells[3].text_content(),
                    # "attorney": cells[2].text_content(), #not yet implemented
                    # "panel": cells[1].text_content(), #need to implement
                }
            )

    def _download_backwards(self, dates: tuple) -> None:
        logger.info("Backscraping for range %s %s", *dates)
        self.d, _ = dates
        self.url = "https://media.cadc.uscourts.gov/recordings/bydate/{yearmo}".format(
            yearmo=self.d.strftime("%Y/%m")
        )
        self.html = self._download()
        self._process_html()
