# Scraper for California's First District Court of Appeal
# CourtID: calctapp_1st
# Court Short Name: Cal. Ct. App.
from datetime import datetime

from juriscraper.opinions.united_states.state import cal


class Site(cal.Site):
    court_code = "A"
    division = "1st App. Dist."

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.parse()
        return 0

    def get_class_name(self):
        return "calctapp_1st"

    def get_court_name(self):
        return "California Court of Appeals"
