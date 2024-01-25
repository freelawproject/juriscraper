"""Scraper for COURT OF APPEALS OF THE STATE OF NEVADA
CourtID: nevapp

History:
    - 2023-12-13: Created by William E. Palin
"""
from typing import Dict

from juriscraper.opinions.united_states.state import nev


class Site(nev.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

    def correct_court(self, case: Dict) -> bool:
        """Filter out cases based on court

        Check the case number to see if its a COA case or not

        :param case: the case information
        :return: if it is a COA case or not
        """
        if "COA" in case["caseNumber"]:
            return True
