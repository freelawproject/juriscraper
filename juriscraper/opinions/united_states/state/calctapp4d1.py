# Scraper for California's Fourth District Court of Appeal Division 1
# CourtID: calctapp4d1
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp1d


class Site(calctapp1d.Site):
    court_code = "D"
    division = "4th App. Dist. Div. 1"
