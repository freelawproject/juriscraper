# Scraper for California's Sixth District Court of Appeal
# CourtID: calctapp6d
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp1d


class Site(calctapp1d.Site):
    court_code = "H"
    division = "6th App. Dist."
