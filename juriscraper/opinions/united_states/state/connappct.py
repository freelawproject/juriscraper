"""Scraper for Connecticut Appellate Court
CourtID: connctapp
Court Short Name: Connappct.
Author: Asadullah Baig<asadullahbeg@outlook.com>
Date created: 2014-07-11
History:
- 2022-02-02, satsuki-chan: Fixed docket and name separator, changed super class to OpinionSiteLinear
"""

from datetime import date

from juriscraper.opinions.united_states.state import conn


class Site(conn.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        current_year = date.today().strftime("%y")
        self.url = f"http://www.jud.ct.gov/external/supapp/archiveAROap{current_year}.htm"
