"""
Author: Krist Jin
History:
  2013-08-18: Created.
  2014-07-17: Updated by mlr to remedy InsanityException.
  2021-11-02: Updated by satsuki-chan: Updated to new page design.
"""
import re
from typing import List

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
            m = re.search(self.docket_re, case["neutral_citation"])
            raw_docket = m.group("docket")
            district = m.group("district")
            docket = f"{district}-{raw_docket[0:2]}-{raw_docket[2:]}"
            dockets_numbers.append(docket)
        return dockets_numbers
