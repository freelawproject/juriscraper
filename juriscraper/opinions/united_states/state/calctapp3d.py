# Scraper for California's Third District Court of Appeal
# CourtID: calctapp3d
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp1d


class Site(calctapp1d.Site):
    court_code = "C"
    division = "3rd App. Dist."
