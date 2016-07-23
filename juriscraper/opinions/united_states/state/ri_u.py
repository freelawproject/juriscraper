"""Scraper for the Rhode Island Supreme Court
CourtID: ri
Court Short Name: R.I.
Author: Brian W. Carver
Date created: 2013-08-10
"""

from juriscraper.opinions.united_states.state import ri_p


class Site(ri_p.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.include_summary = False
        self.precedential_status = 'Unpublished'

    def base_url(self):
        return 'http://www.courts.ri.gov/Courts/SupremeCourt/Pages/Orders/Orders'

    def _get_summaries(self):
        # No summaries for unpublished, just short-circuit.
        return None
