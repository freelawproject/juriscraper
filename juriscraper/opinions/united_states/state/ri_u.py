"""Scraper for the Rhode Island Supreme Court
CourtID: ri
Court Short Name: R.I.
Court Contact: (see ri_p)
Author: Brian W. Carver
History:
    Date created: 2013-08-10 by Brian W. Carver
    2022-05-02: Updated by flooie, to use JSON responses
"""

from juriscraper.opinions.united_states.state import ri_p


class Site(ri_p.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Unpublished"
        self.opinion_type = "Orders"
        self.url = self.build_url()
