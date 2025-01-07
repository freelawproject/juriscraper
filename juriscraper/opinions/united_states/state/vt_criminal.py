"""Scraper for the Vermont Environmental
CourtID: vt
Court Short Name: VT
Court Contact: submit form here https://www.vermontjudiciary.org/website-feedback-form
"""

from . import vt


class Site(vt.Site):
    division = 2
    days_interval = 200

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

    def get_class_name(self):
        return "vt_criminal"

    def get_court_name(self):
        return "Superior Court of Vermont Criminal Division"

