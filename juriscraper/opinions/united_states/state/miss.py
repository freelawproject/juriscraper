"""Scraper for Mississippi Supreme Court
CourtID: miss
Court Contact: bkraft@courts.ms.gov (see https://courts.ms.gov/aoc/aoc.php)
Author: ryee
Reviewer: mlr
History:
    2013-04-26: Created by ryee
    2021-12-17: Updated by flooie
"""

from ast import literal_eval
from datetime import datetime

from lxml.html import tostring

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
        self.court = "SCT"

    def _download(self, request_dict={}) -> None:

        if self.test_mode_enabled():
            self.date = "02/28/2020"  # some random date for testing
            self.html = super()._download()
            self._process_html()
            return

        self.parameters = {"court": self.court}
        dates = super()._download(request_dict)
        dates = literal_eval(dates.xpath("//p")[0].text_content())
        dates.sort(
            key=lambda date: datetime.strptime(date, "%m-%d-%Y"), reverse=True
        )

        # Check the last five dates.
        for date in dates[:5]:
            self.date = date
            self.parameters["date"] = date
            self.url = (
                "https://courts.ms.gov/appellatecourts/docket/get_hd_file.php"
            )
            self.html = super()._download()
            self._process_html()

    def _process_html(self) -> None:
        """Process the HTML for each calendar date.

        :return:None
        """
        if self.html is None:
            return
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
