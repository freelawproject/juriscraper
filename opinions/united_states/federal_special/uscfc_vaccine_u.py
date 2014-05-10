"""Scraper for the United States Court of Federal Claims
CourtID: uscfc
Court Short Name: Fed. Cl."""

import uscfc
import datetime
from datetime import date


class Site(uscfc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscfc.uscourts.gov/aggregator/sources/11'
        self.court_id = self.__module__

    def _get_precedential_statuses(self):
        return ['Unpublished'] * len(self.case_names)

    def _download_backwards(self, page):
        self.url = 'http://www.uscfc.uscourts.gov/aggregator/sources/11?page=' % page
        self.html = self._download()
