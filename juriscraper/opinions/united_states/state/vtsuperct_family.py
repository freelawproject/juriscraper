"""Scraper for the Vermont Environmental
CourtID: vt
Court Short Name: VT
Court Contact: submit form here https://www.vermontjudiciary.org/website-feedback-form
"""

from . import vt


class Site(vt.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.division = 4
        self.url = f"https://www.vermontjudiciary.org/opinions-decisions?f%5B0%5D=court_division_opinions_library_%3A{self.division}"  # supreme
