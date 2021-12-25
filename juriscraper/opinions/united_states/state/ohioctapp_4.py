"""Scraper for the 4th District Court of Appeals
CourtID: ohio
Court Short Name: Ohio
Author: Andrei Chelaru
"""

from juriscraper.opinions.united_states.state import ohio


class Site(ohio.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.data["ctl00$MainContent$ddlCourt"] = 4
