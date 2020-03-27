"""Scraper for the Rhode Island Supreme Court
CourtID: ri
Court Short Name: R.I.
Court Contact: (see ri_p)
Author: Brian W. Carver
Date created: 2013-08-10
"""

from juriscraper.opinions.united_states.state import ri_p


class Site(ri_p.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.include_summary = False
        self.status = "Unpublished"
        self.url = self.build_url(
            "https://www.courts.ri.gov/Courts/SupremeCourt/Pages/Orders/Orders"
        )

    def _get_summaries(self):
        # No summaries for unpublished, just short-circuit.
        return None
