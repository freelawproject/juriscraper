"""Scraper for Court of Appeals of Kentucky
CourtID: kyctapp
Court Short Name: Ky. Ct. App.
Contact: https://courts.ky.gov/aoc/technologyservices/Pages/ContactTS.aspx

"""

from juriscraper.opinions.united_states.state import ky


class Site(ky.Site):
    api_court = "Kentucky Court of Appeals"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
