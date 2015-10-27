#  Scraper for Kansas Appeals Court
# CourtID: kanctapp
# Court Short Name: kanctapp
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 25 July 2014


from juriscraper.opinions.united_states.state import kan


class Site(kan.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_index = 2
