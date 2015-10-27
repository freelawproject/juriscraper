#  Scraper for Florida 1st District Court of Appeal
# CourtID: flaapp1
# Court Short Name: flaapp1
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 21 July 2014

from juriscraper.opinions.united_states.state import fladistctapp_1_per_curiam


class Site(fladistctapp_1_per_curiam.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.opinion_type = 'Written'
