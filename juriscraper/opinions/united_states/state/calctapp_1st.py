# Scraper for California's First District Court of Appeal
# CourtID: calctapp_1st
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import cal


class Site(cal.Site):
    court_code = "A"
    division = "1st App. Dist."
