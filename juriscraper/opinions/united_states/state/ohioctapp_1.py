"""Scraper for the 1st District Court of Appeals
CourtID: ohioctap_1
Court Short Name: Ohio Dist Ct App 1
Author: Andrei Chelaru
"""

from juriscraper.opinions.united_states.state import ohio


class Site(ohio.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_index = 1
