# coding=utf-8
"""Scraper for Colorado Appeals Court
CourtID: coloctapp
Court Short Name: Colo. Ct. App.
History:
 - 2014-07-11, author: Asadullah Baig<asadullahbeg@outlook.com>
 - Reviewer: mlr
 - 2015-07-30: Fixed by mlr.
"""

from juriscraper.opinions.united_states.state import colo


class Site(colo.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.cobar.org/For-Members/Opinions-Rules-Statutes/Colorado-Court-of-Appeals-Opinions"
        self.base_path = "//div[@id='dnn_ctr2514_ModuleContent']/ul/li/a"
