# coding=utf-8
"""Scraper for Connecticut Appellate Court
CourtID: connctapp
Court Short Name: Connctapp.
Author: Asadullah Baig<asadullahbeg@outlook.com>
Date created: 2014-07-11
"""

from datetime import date
from juriscraper.opinions.united_states.state import conn

class Site(conn.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.crawl_date = date.today()
        self.url = 'http://www.jud.ct.gov/external/supapp/archiveAROap{year}.htm'.format(year=self.crawl_date.strftime("%y"))
        self.court_id = self.__module__
