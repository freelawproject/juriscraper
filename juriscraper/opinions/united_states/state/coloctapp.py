# coding=utf-8
"""Scraper for Colorado Appeals Court
CourtID: coloctapp
Court Short Name: Colo. Ct. App.
History:
 - 2014-07-11, author: Asadullah Baig<asadullahbeg@outlook.com>
 - Reviewer: mlr
 - 2015-07-30: Fixed by mlr.
"""

from datetime import date

from juriscraper.opinions.united_states.state import colo


class Site(colo.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.cobar.org/opinions/index.cfm?courtid=1'
        # For testing
        #self.url = 'http://www.cobar.org/opinions/opinionlist.cfm?casedate=7/31/2014&courtid=1'
        self.court_id = self.__module__

    def _get_summaries(self):
        return None

    def _get_nature_of_suit(self):
        return None
