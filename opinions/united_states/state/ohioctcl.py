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
        self.court_index = 13
        self.back_scrape_iterable = range(1992, 2014)
        self.url = self.make_url(self.court_index, self.year)
