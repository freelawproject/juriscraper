"""Scraper for the 7th District Court of Appeals
CourtID: ohioctap_7
Court Short Name: Ohio Dist Ct App 7
Author: Andrei Chelaru
"""

from juriscraper.opinions.united_states.state import ohio


class Site(ohio.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_index = 7

    def get_class_name(self):
         return "ohioctapp_7"

    def get_court_name(self):
         return "Ohio Court of Appeals"
