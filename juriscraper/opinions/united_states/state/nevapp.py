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
        self.court_code = "10002"

    def filter_cases(self):
        """"""
        cases = []
        for case in self.html:
            advances = [case["advanceNumber"] for case in cases]
            if (
                "COA" not in case["caseNumber"]
                or case["advanceNumber"] in advances
            ):
                continue
            cases.append(case)
        return cases[:20]
