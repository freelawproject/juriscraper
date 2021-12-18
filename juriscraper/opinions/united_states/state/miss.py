"""Scraper for Mississippi Supreme Court
CourtID: miss
Court Contact: bkraft@courts.ms.gov (see https://courts.ms.gov/aoc/aoc.php)
Author: ryee
Reviewer: mlr
History:
    2013-04-26: Created by ryee
    2021-12-17: Updated by flooie
"""
import json
from datetime import datetime

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


# Landing page: https://courts.ms.gov/appellatecourts/sc/scdecisions.php
class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://courts.ms.gov/appellatecourts/docket/gethddates.php"
        )
        self.method = "POST"
        self.date = None
        self.dates = None
        self.court = "SCT"

    def _download(self, request_dict={}) -> None:
        """Download the HTML for the site."""
        if self.test_mode_enabled():
            self.date = "02/28/2020"  # some random date for testing
            self.dates = ["02/28/2020"]
            return super()._download()
        if not self.dates:
            self.parameters = {"court": self.court}
        return super()._download(request_dict)

    def make_dates(self) -> None:
        """Get last five dates sort and download them

        :param html:The HTML for the initial call to the site
        :return:None
        """
        dates = json.loads(self.html.xpath("//p/text()")[0])
        dates.sort(
            key=lambda date: datetime.strptime(date, "%m-%d-%Y"), reverse=True
        )
        self.dates = dates[:5]

    def _process_html(self) -> None:
        """Process the HTML for each calendar date.

        :return:None
        """

        # Find the last five dates
        if not self.dates:
            self.make_dates()

        # Iterate over the dates to generate the HTML to parse
        for date in self.dates:
            if not self.test_mode_enabled():
                self.date = date
                self.parameters["date"] = self.date
                self.url = "https://courts.ms.gov/appellatecourts/docket/get_hd_file.php"
                self.html = super()._download()

            rows = self.html.xpath(".//body/b") + self.html.xpath(".//body/p")
            for row in rows:
                links = row.xpath(".//a[contains(@href, '.pdf')]")
                if not links:
                    continue
                case_info = row.xpath(".//following-sibling::ul")[0]
                name, summaries = case_info.xpath(".//text()")
                self.cases.append(
                    {
                        "name": name,
                        "date": self.date,
                        "docket": links[0].text_content().strip(),
                        "url": links[0].attrib["href"],
                        "status": "Published",
                        "summary": summaries,
                    }
                )
