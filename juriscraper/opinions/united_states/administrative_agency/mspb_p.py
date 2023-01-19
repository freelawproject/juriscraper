"""Scraper for U.S. Merit Systems Protection Board
CourtID: mspb
Court Short Name: MSPB
Author: Jon Andersen
Reviewer: mlr
Date created: 1 Sep 2014
Type: Precedential
"""
import json

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://www.mspb.gov/decisions/precedential/PrecedentialDecisions_Manifest_Table.json"
        self.base = "https://www.mspb.gov/decisions/precedential"

    def _process_html(self):
        if self.test_mode_enabled():
            self.html = json.load(open(self.url))
        for row in self.html["data"]:
            url = row["FILE_NAME"]
            name = f"{row['APL_FIRST_NAME']} {row['APL_LAST_NAME']} v. {row['AGENCY']}"
            self.cases.append(
                {
                    "citation": row["DECISION_NUMBER"],
                    "url": f"{self.base}/{url}",
                    "docket": row["DOCKET_NBR"],
                    "name": name,
                    "date": row["ISSUED_DATE"].replace("/", "-"),
                }
            )
