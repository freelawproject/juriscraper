# Scraper for California's Second District Court of Appeal
# CourtID: calctapp_2nd
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp_1st


class Site(calctapp_1st.Site):
    court_code = "B"
    division = "2nd App. Dist."
