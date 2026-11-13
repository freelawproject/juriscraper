# Scraper for California's Fourth District Court of Appeal Division 2
# CourtID: calctapp4d2
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp1d


class Site(calctapp1d.Site):
    court_code = "E"
    division = "4th App. Dist. Div. 2"
