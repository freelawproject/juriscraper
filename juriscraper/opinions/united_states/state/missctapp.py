"""Scraper for Mississippi Court of Appeals
CourtID: missctapp
Court Short Name: Miss. Ct. App.
"""

from juriscraper.opinions.united_states.state import miss


class Site(miss.Site):
    def get_court_parameter(self):
        return "COA"
