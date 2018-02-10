# Scraper for Florida 1st District Court of Appeal Written
# CourtID: flaapp1
# Court Short Name: flaapp1

import fladistctapp_1_per_curiam


class Site(fladistctapp_1_per_curiam.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.type_id = 1  # Written
        self.url = self.get_url()
