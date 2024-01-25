"""Scraper for COURT OF APPEALS OF THE STATE OF NEVADA
CourtID: nevapp

History:
    - 2023-12-13: Created by William E. Palin
"""

from juriscraper.opinions.united_states.state import nev


class Site(nev.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

    def correct_court(self, case):
        if "COA" in case["caseNumber"]:
            return True
