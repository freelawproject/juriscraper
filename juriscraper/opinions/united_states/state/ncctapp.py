"""Scraper for North Carolina Court of Appeals
CourtID: ncctapp
Court Short Name: N.C. Ct. App.
Author: Jon Andersen
History:
    2014-08-04: Created by Jon Andersen
"""

from datetime import date

from juriscraper.opinions.united_states.state import nc


class Site(nc.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://appellate.nccourts.org/opinions/?c=coa&year=%s' % date.today().year
        self.back_scrape_iterable = range((date.today().year - 1), 1997, -1)

    def _download_backwards(self, year):
        self.url = 'http://appellate.nccourts.org/opinions/?c=coa&year=%s' % year
        self.html = self._download()
