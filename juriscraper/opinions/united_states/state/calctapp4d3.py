# Scraper for California's Fourth District Court of Appeal Division 3
# CourtID: calctapp4d3
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp1d


class Site(calctapp1d.Site):
    court_code = "G"
    division = "4th App. Dist. Div. 3"
