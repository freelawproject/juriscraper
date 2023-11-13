# Scraper for Florida 6th District Court of Appeal
# CourtID: flaapp6
# Court Short Name: flaapp6

from . import fladistctapp


class Site(fladistctapp.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.number = "sixth"
        self.base = "https://6dca.flcourts.gov"
        self.update_url()
