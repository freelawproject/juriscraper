"""Scraper for the United States Court of Federal Claims
CourtID: uscfc
Court Short Name: Fed. Cl."""

import uscfc

class Site(uscfc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = (
            'http://www.uscfc.uscourts.gov/opinions_decisions_general/Unpublished')
        self.court_id = self.__module__

    def _get_precedential_statuses(self):
        return ['Unpublished'] * len(self.case_names)