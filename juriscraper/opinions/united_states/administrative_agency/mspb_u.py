"""Scraper for U.S. Merit Systems Protection Board
CourtID: mspb
Court Short Name: MSPB
Author: Jon Andersen
Reviewer: mlr
Date created: 1 Sep 2014
Type: Non-precedential
"""

import random
from juriscraper.opinions.united_states.administrative_agency import mspb_p


class Site(mspb_p.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.mspb.gov/netsearch/decisiondisplay_2011.aspx?timelapse=3&displaytype=60414&description=Nonprecedential%20Decisions&cachename=a' + str(random.randrange(1, 100000000))
        self.column_diff = -1

    def _get_precedential_statuses(self):
        return ["Unpublished"] * len(self.case_dates)

    def _get_neutral_citations(self):
        return None
