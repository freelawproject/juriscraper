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

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "http://www.asbca.mil/Decisions/decisions%d.html"
            % datetime.today().year
        )
        self.status = "Published"

    def _process_html(self):
        for row in self.html.xpath(".//tr")[1:]:
            col1, col2, col3, col4 = row.xpath(".//td")
            date = col1.text_content().strip()
            if not col2.text_content().strip():
                continue
            name = col3.text_content().strip()
            docket = col2.text_content().strip()
            url = col3.xpath(".//a/@href")[0]
            self.cases.append(
                {"date": date, "name": name, "url": url, "docket": docket}
            )
