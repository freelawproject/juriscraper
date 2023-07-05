"""Scraper for the Maryland Attorney General
CourtID: mdag
Court Short Name: Maryland Attorney General
"""

import json
import re
from datetime import date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.marylandattorneygeneral.gov/_layouts/15/inplview.aspx"
        )
        self.year = date.today().year

        self.parameters = {
            "List": "{1BA692B1-E50C-4754-AADD-E6753F46B403}",
            "View": "{E1A60D10-12C0-4029-8BE0-BA5F9AC93BF8}",
            "ViewCount": "50",  # results to return
            "IsXslView": "TRUE",
            "IsCSR": "TRUE",
            "GroupString": f";#{self.year};#",
            "IsGroupRender": "TRUE",
        }
        self.status = "Published"

    def _download(self, request_dict={}):
        if self.test_mode_enabled():
            with open(self.url) as file:
                self.json = json.load(file)
        else:
            self.json = (
                self.request["session"]
                .post(self.url, params=self.parameters)
                .json()
            )

    def _process_html(self):
        for row in self.json["Row"]:
            url_path = row["FileRef.urlencodeasurl"]

            # created_x0020_date looks like this 0;#2021-11-09 14:29:09
            datetime_string = row["Created_x0020_Date"]
            date = re.findall(r"\d{4}-\d{2}-\d{2}", datetime_string)[0]
            self.cases.append(
                {
                    "docket": row["Title"],
                    "summary": row["Summary"],
                    "name": row["FileLeafRef.Name"],
                    "url": f"https://www.marylandattorneygeneral.gov{url_path}",
                    "date": date,
                }
            )
