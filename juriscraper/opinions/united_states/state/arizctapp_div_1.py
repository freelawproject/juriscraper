"""Scraper for the Court of Appeals of Arizona, Division 1
CourtID: arizctapp_div_1
Court Short Name: Ariz. Ct. App.

History:
    2014-02-14: Created by Deb Linton
    2026-01-05: Rewritten to use new API by Luis Manzur
"""

from juriscraper.opinions.united_states.state import ariz


class Site(ariz.Site):
    base_url = "https://coa1.azcourts.gov"
    court_param = "Division1"
    search_page_path = "/Decisions/Search-Decisions"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
