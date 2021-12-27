# Scraper for California's Fourth District Court of Appeal Division 2
# CourtID: calctapp_4th_div2
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp_1st


class Site(calctapp_1st.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_code = "E"
        self.division = "4th App. Dist. Div. 2"
