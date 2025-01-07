"""Scraper for the Vermont Environmental
CourtID: vt
Court Short Name: VT
Court Contact: submit form here https://www.vermontjudiciary.org/website-feedback-form
"""

from juriscraper.opinions.united_states.state import vtsuperct_civil


class Site(vtsuperct_civil.Site):
    division = 4
    days_interval = 360

    def get_class_name(self):
        return "vtsuperct_family"

    def get_court_name(self):
        return "Superior Court of Vermont Family Division"
