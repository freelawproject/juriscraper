# Scraper for California's Superior Court Appellate Division
# CourtID: calctapp_app_div
# Court Short Name: Cal. Ct. App.
from datetime import datetime

from juriscraper.opinions.united_states.state import calctapp_1st


class Site(calctapp_1st.Site):
    court_code = "J"
    division = "App. Div."

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.parse()
        return 0

    def get_class_name(self):
        return "calctapp_app_div"

    def get_court_name(self):
        return "California Superior Court Appellate Division"
