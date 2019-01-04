# Scraper for Florida 2nd District Court of Appeal Written
# CourtID: flaapp2
# Court Short Name: flaapp2

from . import fladistctapp_2_per_curiam


class Site(fladistctapp_2_per_curiam.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.type_id = 1  # Written
        self.url = self.get_url()
