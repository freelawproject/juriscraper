# Scraper for Florida 3rd District Court of Appeal Per Curiam
# CourtID: flaapp3
# Court Short Name: flaapp3

from . import fladistctapp


class Site(fladistctapp.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.number = "third"
        self.base = "https://3dca.flcourts.gov"
        self.update_url()
