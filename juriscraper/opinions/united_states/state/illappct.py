"""
Scraper for Illinois Appellate Court
CourtID: illappct
Author: Krist Jin
History:
  2013-08-18: Created.
  2014-07-17: Updated by mlr to remedy InsanityException.
  2021-11-02: Updated by satsuki-chan: Updated to new page design.
  2021-12-30: Updated by satsuki-chan: Added validation when citation is missing.
"""
import re
from typing import List

from juriscraper.AbstractSite import logger
from juriscraper.lib.exceptions import InsanityException
from juriscraper.opinions.united_states.state import ill


class Site(ill.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.illinoiscourts.gov/top-level-opinions?type=appellate"
        )

    def _get_docket_numbers(self) -> List[str]:
        """Get the docket number from citation.

        Extract district and docket number to construct the full docket number.

        Returns: List of docket numbers
        """
        dockets_numbers = []
        for case in self.cases:
            match = re.search(self.docket_re, case["neutral_citation"])
            if match:
                raw_docket = match.group("docket")
                district = match.group("district")
                docket = f"{district}-{raw_docket[0:2]}-{raw_docket[2:]}"
                dockets_numbers.append(docket)
            else:
                logger.info(f"Could not find docket for case: '{case}'")
                raise InsanityException(
                    f"Could not find docket for case: '{case}'"
                )
        return dockets_numbers
