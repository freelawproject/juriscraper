"""Scraper for Vermont Supreme Court decisions filed under the Criminal Division
CourtID: vt
Court Short Name: VT
Court Contact: submit form here https://www.vtcourts.gov/website-feedback-form
"""

from . import vt


class Site(vt.Site):
    division = 2
    days_interval = 200

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
