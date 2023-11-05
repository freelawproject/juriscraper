# Scraper for Florida 1st District Court of Appeal Per Curiam
# CourtID: flaapp1
# Court Short Name: flaapp1

from . import fladistctapp


class Site(fladistctapp.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.number = "first"
        self.base = "https://1dca.flcourts.gov"
        self.update_url()
