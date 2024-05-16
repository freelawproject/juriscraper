# Scraper for California's Superior Court Appellate Division
# CourtID: calctapp_app_div
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp_1st


class Site(calctapp_1st.Site):
    court_code = "J"
    division = "App. Div."
