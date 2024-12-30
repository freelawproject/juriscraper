# Scraper for California's Third District Court of Appeal
# CourtID: calctapp_3rd
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp_1st


class Site(calctapp_1st.Site):
    court_code = "C"
    division = "3rd App. Dist."
