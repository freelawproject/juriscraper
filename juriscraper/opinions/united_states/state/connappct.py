"""Scraper for Connecticut Appellate Court
CourtID: connctapp
Court Short Name: Connappct.
Author: Asadullah Baig<asadullahbeg@outlook.com>
Date created: 2014-07-11
"""

from datetime import date
from juriscraper.opinions.united_states.state import conn


class Site(conn.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.crawl_date = date.today()
        self.url = "http://www.jud.ct.gov/external/supapp/archiveAROap{year}.htm".format(
            year=self.crawl_date.strftime("%y")
        )
        self.court_id = self.__module__
