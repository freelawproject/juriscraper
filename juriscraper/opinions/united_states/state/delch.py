#  Scraper for the Court Of Chancery of Delaware
# CourtID: dechan
# Court Short Name: De.
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 31 July 2014

from juriscraper.opinions.united_states.state import delaware


class Site(delaware.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court="Court of Chancery"
        self.court_id = self.__module__

    def get_class_name(self):
        return "delch"

    def get_court_name(self):
        return "Delaware Court of Chancery"
