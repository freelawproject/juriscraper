#  Scraper for Kansas Appeals Court
# CourtID: kanctapp
# Court Short Name: kanctapp
# Author: Andrei Chelaru
# Reviewer:
# Date created: 25 July 2014


from datetime import date

from juriscraper.opinions.united_states.state import kan


class Site(kan.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.court_index = 2