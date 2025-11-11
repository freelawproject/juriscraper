# Scraper for New York Appellate Divisions 3rd Dept.
# CourtID: nyappdiv_3rd
# Court Short Name: NY
from datetime import date

from juriscraper.opinions.united_states.state import nyappdiv_1st


class Site(nyappdiv_1st.Site):
    first_opinion_date = date(2003, 9, 25)
    days_interval = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "App Div, 3d Dept"
        self._set_parameters()
