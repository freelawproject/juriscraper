"""Scraper for the 8th District Court of Appeals
CourtID: ohioctap_8
Court Short Name: Ohio Dist Ct App 8
Author: Andrei Chelaru
"""

from juriscraper.opinions.united_states.state import ohio


class Site(ohio.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_index = 8
