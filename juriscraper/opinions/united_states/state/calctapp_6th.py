# Scraper for California's Sixth District Court of Appeal
# CourtID: calctapp_6th
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp_1st


class Site(calctapp_1st.Site):
    court_code = "H"
    division = "6th App. Dist."
