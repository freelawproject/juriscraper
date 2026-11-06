# Scraper for California's Fifth District Court of Appeal
# CourtID: calctapp5d
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp1d


class Site(calctapp1d.Site):
    court_code = "F"
    division = "5th App. Dist."
