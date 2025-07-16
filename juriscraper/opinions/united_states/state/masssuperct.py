"""
Scraper for Massachusetts Superior Court
CourtID: masssuperct
Court Short Name: MS
Author: Luis Manzur
Court Contact: SJCReporter@sjc.state.ma.us (617) 557-1030
Date: 2025-07-16
History:
    - Created by luism
"""

from juriscraper.opinions.united_states.state import mass


class Site(mass.Site):
    court_name = "Superior Court"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
