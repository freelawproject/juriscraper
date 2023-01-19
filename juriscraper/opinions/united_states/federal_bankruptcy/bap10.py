"""
Scraper for the United States Bankruptcy Appellate Panel for the Tenth Circuit
CourtID: bap10
Court Short Name: 10th Cir. BAP
Auth: Jon Andersen <janderse@gmail.com>
Reviewer: mlr
History:
    2014-09-01: First draft by Jon Andersen
    2014-09-02: Revised by mlr to use _clean_text() instead of pushing logic
                into the _get_case_dates function.
"""

from datetime import date, timedelta
from urllib.parse import urlencode

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.bap10.uscourts.gov/opinion/search/results"
        self.court_id = self.__module__
        today = date.today()
        params = urlencode(
            {
                "keywords": "",
                "parties": "",
                "judges": "",
                "field_opinion_date_value[min][date]": (
                    today - timedelta(30)
                ).strftime("%m/%d/%Y"),
                "field_opinion_date_value[max][date]": today.strftime(
                    "%m/%d/%Y"
                ),
                "exclude": "",
            }
        )
        self.url = (
            f"https://www.bap10.uscourts.gov/opinion/search/results?{params}"
        )

    def _process_html(self):
        for row in self.html.xpath(".//tr"):
            if not row.xpath(".//td"):
                continue
            self.cases.append(
                {
                    "docket": row.xpath(".//td")[0].text_content().strip(),
                    "name": row.xpath(".//td")[1].text_content().strip(),
                    "date": row.xpath(".//td")[2].text_content().strip(),
                    "url": row.xpath(".//a/@href")[0],
                    "status": "Published",
                }
            )
