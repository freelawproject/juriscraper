"""Scraper for Connecticut Appellate Court
CourtID: connctapp
Court Short Name: Connappct.
Author: Asadullah Baig<asadullahbeg@outlook.com>
Date created: 2014-07-11
History:
    - 2022-02-02, satsuki-chan: Updated to Opinionsitelinear
    - 2023-11-20, William Palin: Updated
"""

from juriscraper.opinions.united_states.state import conn


class Site(conn.Site):

    court_abbv = "ap"

    def __init__(self, *args, **kwargs):
        print("inside the class connctapp")
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

    def get_court_name(self):
        return "Appellate Court of Connecticut"

    def get_class_name(self):
        return "connappct"
