#  Scraper for the Court Of Common Pleas of Delaware
# CourtID: dectcompl
# Court Short Name: De.
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 31 July 2014

from juriscraper.opinions.united_states.state import delaware


class Site(delaware.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court="Court of Common Pleas"
        self.court_id = self.__module__

    def get_class_name(self):
        return "delctcompl"

    def get_court_name(self):
        return "Court of Common Pleas"
