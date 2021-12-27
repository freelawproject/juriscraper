# Scraper for California's Superior Court Appellate Division
# CourtID: calctapp_app_div
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp_1st


class Site(calctapp_1st.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_code = "J"
        self.division = "App. Div."
