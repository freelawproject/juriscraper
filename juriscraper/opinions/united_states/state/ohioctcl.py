"""Scraper for the Ohio Ct of Claims
CourtID: ohioctcl
Court Short Name: Ohio Ct of Cl
Author: Andrei Chelaru
"""

from juriscraper.opinions.united_states.state import ohio


class Site(ohio.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_index = 13
