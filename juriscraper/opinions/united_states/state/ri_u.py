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
        self.url = 'http://www.courts.ri.gov/Courts/SupremeCourt/Pages/Orders/Orders{current}-{next}' \
                   '.aspx'.format(
            current=self.current_year,
            next=self.current_year + 1,
        )

    def _get_precedential_statuses(self):
        return ['Unpublished'] * len(self.case_names)

    def _get_summaries(self):
        # No summaries for unpublished, just short-circuit.
        return None
