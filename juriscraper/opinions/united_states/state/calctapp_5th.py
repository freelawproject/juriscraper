# Scraper for California's Fifth District Court of Appeal
# CourtID: calctapp_5th
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp_1st


class Site(calctapp_1st.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_code = "F"
        self.division = "5th App. Dist."
