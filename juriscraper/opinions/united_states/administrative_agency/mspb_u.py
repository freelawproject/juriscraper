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
        self.type = "Nonprecedential"
        self.display = 60414
        self.column_diff = -1
        self.set_url()

    def _get_precedential_statuses(self):
        return ["Unpublished"] * len(self.case_dates)

    def _get_citations(self):
        return None
