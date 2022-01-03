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
        Examples:
            Citation                      - Docket
            "2018 IL App (5th) 150159-UB" - 5-15-0159
            "2014 IL App (4th) 131281"    - 4-13-1281
            "2019 IL App (3d) 180261-U"   - 3-18-0261
            "2020 IL App (2d) 190759WC-U" - 2-19-0759WC
            "2021 IL App (1st) 131973-B"  - 1-13-1973
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
                logger.critical(f"Could not find docket for case: '{case}'")
                continue
        return dockets_numbers
