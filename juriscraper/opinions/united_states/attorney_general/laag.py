"""
Scraper for Louisiana Attorney General
CourtID: laag
Court Short Name: Louisiana AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""

from datetime import date, timedelta

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://www.ag.state.la.us/Opinion/Search"
        self.td = date.today()
        self.parameters = {
            "SearchTerm": "",
            "StartDate": (self.td - timedelta(days=31)).strftime("%m/%d/%Y"),
            "EndDate": self.td.strftime("%m/%d/%Y"),
        }
        self.method = "POST"

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//a/.."):
            name = row.xpath(".//h5/text()")[0]
            url = row.xpath(".//a/@href")[0]
            date = row.xpath(".//b/text()")[-1].split(":")[-1]
            self.cases.append(
                {"url": url, "docket": name, "name": name, "date": date}
            )
