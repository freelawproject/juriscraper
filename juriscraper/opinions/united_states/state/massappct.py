# Scraper for Massachusetts Appeals Court
# CourtID: massapp
#Court Short Name: MS
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-12

from juriscraper.opinions.united_states.state import mass


class Site(mass.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_identifier = 'AC'
        # If you discover new examples that failed the
        # regex below, please add them to the test_massappct
        # method in test_everything.py
        self.regex = "(.*) \((%s.*?)\)" % self.court_identifier
        self.date_group = 3
        self.set_local_variables()
