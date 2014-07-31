"""Scraper for the 1st District Court of Appeals
CourtID: ohio
Court Short Name: Ohio
Author: Andrei Chelaru
"""

from juriscraper.opinions.united_states.state import ohio


class Site(ohio.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.court_index = 9
        self.url = self.make_url(self.court_index)
