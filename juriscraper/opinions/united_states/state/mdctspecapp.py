"""
Scraper for Maryland Court of Special Appeals
CourtID: mdctspecapp
Court Short Name: MD
Author: Andrei Chelaru
Date created: 06/27/2014
"""

from juriscraper.opinions.united_states.state import md


class Site(md.Site):
    court = "cosa"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
