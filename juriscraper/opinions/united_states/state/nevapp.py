"""Scraper for COURT OF APPEALS OF THE STATE OF NEVADA
CourtID: nevapp

History:
    - 2023-12-13: Created by William E. Palin
"""
from juriscraper.opinions.united_states.state import nev


class Site(nev.Site):
    def _process_html(self):
        for case in self.html:
            if "COA" not in case["caseNumber"]:
                continue
            self.cases.append(
                {
                    "name": case["caseTitle"],
                    "docket": case["caseNumber"],
                    "date": case["date"],
                    "url": case["docurl"],
                }
            )
