# Scraper for Florida 2nd District Court of Appeal Per Curiam
# CourtID: flaapp2
# Court Short Name: flaapp2

from . import fladistctapp


class Site(fladistctapp.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.number = "second"
        self.base = "https://2dca.flcourts.gov"
        self.update_url()
