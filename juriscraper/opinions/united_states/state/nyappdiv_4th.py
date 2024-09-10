# Scraper for New York Appellate Divisions 4th Dept.
# CourtID: nyappdiv_4th
from datetime import date

from juriscraper.opinions.united_states.state import ny
from juriscraper.OpinionSite import OpinionSite


class Site(ny.Site):
    first_opinion_date = date(2003, 9, 25)
    days_interval = 30
    extract_from_text = OpinionSite.extract_from_text

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "App Div, 4th Dept"
        self._set_parameters()
