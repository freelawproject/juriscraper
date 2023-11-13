# Scraper for Florida 4th District Court of Appeal Per Curiam
# CourtID: flaapp4
# Court Short Name: flaapp4

from . import fladistctapp


class Site(fladistctapp.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.number = "fourth"
        self.base = "https://4dca.flcourts.gov"
        self.update_url()
