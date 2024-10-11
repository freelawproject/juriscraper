# Scraper for California's Second District Court of Appeal
# CourtID: calctapp_2nd
# Court Short Name: Cal. Ct. App.
from datetime import datetime

from juriscraper.opinions.united_states.state import calctapp_1st


class Site(calctapp_1st.Site):
    court_code = "B"
    division = "2nd App. Dist."

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.parse()
        return 0

    def get_class_name(self):
        return "calctapp_2nd"

    def get_court_name(self):
        return "California Court of Appeals"
