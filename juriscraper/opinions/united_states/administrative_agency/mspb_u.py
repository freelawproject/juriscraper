"""Scraper for U.S. Merit Systems Protection Board
CourtID: mspb
Court Short Name: MSPB
Author: Jon Andersen
Reviewer: mlr
Date created: 1 Sep 2014
Type: Non-precedential
"""

from juriscraper.opinions.united_states.administrative_agency import mspb_p


class Site(mspb_p.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Unpublished"
        self.url = "https://www.mspb.gov/decisions/nonprecedential/NonPrecedentialDecisions_Manifest_Table.json"
        self.base = "https://www.mspb.gov/decisions/nonprecedential/"
