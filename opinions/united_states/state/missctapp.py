"""Scraper for Mississippi Court of Appeals
CourtID: missctapp
Court Short Name: Miss. Ct. App.
Author: Jon Andersen
Reviewer: mlr
Type: Precedential
History:
    2014-09-21: Created by Jon Andersen
"""

from datetime import date

from juriscraper.opinions.united_states.state import miss


class Site(miss.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://courts.ms.gov/scripts/websiteX_cgi.exe/GetOpinion?Year=%s&Court=Court+of+Appeals&Submit=Submit' % date.today().year
        self.back_scrape_iterable = range(2013, 1996 - 1, -1)

    def _download_backwards(self, year):
        self.url = 'http://courts.ms.gov/scripts/websiteX_cgi.exe/GetOpinion?Year=%s&Court=Court+of+Appeals&Submit=Submit' % year
        self.html = self._download()
