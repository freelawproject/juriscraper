# Scraper for California's Second District Court of Appeal
# CourtID: calctapp2d
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp1d


class Site(calctapp1d.Site):
    court_code = "B"
    division = "2nd App. Dist."
