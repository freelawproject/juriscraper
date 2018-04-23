"""Scraper for the Vermont Environmental
CourtID: vt
Court Short Name: VT
Court Contact: submit form here https://www.vermontjudiciary.org/website-feedback-form
"""

import vt


class Site(vt.Site):
    def get_backscrape_max(self):
        return 37

    def get_division_id(self):
        return '1'
