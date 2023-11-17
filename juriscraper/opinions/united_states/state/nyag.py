"""Scraper for the New York Attorney General
CourtID: nyag
Court Short Name: New York Attorney General
"""

import datetime

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = datetime.date.today().year
        self.base_url = "https://ag.ny.gov/appeals-and-opinions/numerical-index?field_opinion_year_value=%d"
        self.url = self.base_url % self.year
        self.status = "Published"

    def _process_html(self):
        """"""
        for row in self.html.xpath("//div[@class='views-row']"):
            docket, _, _, summary, *_ = row.xpath(".//div/text()")
            url = row.xpath(".//div/span/p/a")[0].get("href")
            case = row.xpath(".//div/span/p/a/text()")[0]
            self.cases.append(
                {
                    "name": case,
                    "docket": docket,
                    "url": url,
                    "summary": summary,
                    "date": f"{docket[:4]}-07-01",
                    "date_filed_is_approximate": True,
                }
            )
