"""Scraper for the 2nd District Court of Appeals
CourtID: ohioctap_2
Court Short Name: Ohio Dist Ct App 2
Author: Andrei Chelaru
"""

from juriscraper.opinions.united_states.state import ohio


class Site(ohio.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_index = 2
