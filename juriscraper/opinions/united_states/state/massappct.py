"""
Scraper for Massachusetts Appeals Court
CourtID: massapp
Court Short Name: MS
Author: Andrei Chelaru
Court Contact: SJCReporter@sjc.state.ma.us (617) 557-1030
Reviewer: mlr
Date: 2014-07-12
"""

from juriscraper.opinions.united_states.state import mass


class Site(mass.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_identifier = "AC"
        self.set_local_variables()
