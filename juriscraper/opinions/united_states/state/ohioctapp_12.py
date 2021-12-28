"""Scraper for the 12th District Court of Appeals
CourtID: ohioctap_12
Court Short Name: Ohio Dist Ct App 12
Author: Andrei Chelaru
"""

from juriscraper.opinions.united_states.state import ohio


class Site(ohio.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_index = 12
