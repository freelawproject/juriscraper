"""
Scraper for Illinois Appellate Court
CourtID: illappct
Author: Krist Jin
History:
  2013-08-18: Created.
  2014-07-17: Updated by mlr to remedy InsanityException.
  2021-11-02: Updated by satsuki-chan: Updated to new page design.
  2022-01-21: Updated by satsuki-chan: Added validation when citation is missing.
"""

from juriscraper.opinions.united_states.state import ill


class Site(ill.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.illinoiscourts.gov/top-level-opinions?type=appellate"
        )
        self.docket_re = r"(?P<citation>\d{4}\s+IL App\s+(\((?P<district>\d+)\w{1,2}\)\s+)?(?P<docket>\d+\w{1,2})-?U?[BCD]?)"

    def _get_docket(self, match):
        raw_docket = match.group("docket")
        district = match.group("district")
        return f"{district}-{raw_docket[0:2]}-{raw_docket[2:]}"
