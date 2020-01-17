"""
Scraper for Massachusetts Appeals Court
CourtID: massapp
Court Short Name: MS
Author: William Palin
Court Contact: SJCReporter@sjc.state.ma.us (617) 557-1030
Reviewer:
Date: 2020-01-17
"""

from juriscraper.opinions.united_states.state import mass


class Site(mass.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "https://www.mass.gov/service-details/new-opinions"
        self.court_id = self.__module__
        self.court_identifier = "AC"
        self.set_local_variables()
