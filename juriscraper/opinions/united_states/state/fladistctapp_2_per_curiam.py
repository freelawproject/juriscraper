# Scraper for Florida 2nd District Court of Appeal Per Curiam
# CourtID: flaapp2
# Court Short Name: flaapp2

import fladistctapp_1_per_curiam


class Site(fladistctapp_1_per_curiam.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_number = 2
        self.url = self.get_url()
        self.back_scrape_iterable = [
            (11, 2017),
            (12, 2017),
            (1, 2018),
            (2, 2018),
        ]
