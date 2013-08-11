"""Scraper for the Rhode Island Supreme Court
CourtID: ri
Court Short Name: R.I.
Author: Brian W. Carver
Date created: 2013-08-10
"""

from datetime import date
from datetime import datetime
import ri_p


class Site(ri_p.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.courts.ri.gov/Courts/SupremeCourt/Orders/Orders%20%282012-2013%29.aspx'

    def _get_precedential_statuses(self):
        return ['Unpublished'] * len(self.case_names)

    def _get_summaries(self):
        # No summaries for unpublished, just short-circuit.
        return None
