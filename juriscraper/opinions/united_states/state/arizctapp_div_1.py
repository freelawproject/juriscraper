"""
Author: Deb Linton
Date created: 2014-02-14
Scraper for the Court of Appeals of Arizona, Division 1
CourtID: arizctapp
Court Short Name: Ariz. Ct. App.
"""

from juriscraper.opinions.united_states.state import ariz


class Site(ariz.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.azcourts.gov/opinions/SearchOpinionsMemoDecs.aspx?court=998"
