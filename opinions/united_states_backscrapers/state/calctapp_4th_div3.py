# Backscraper Scraper for California's Fourth District Court of Appeal Division 3
# CourtID: calctapp_4th_div3
# Court Short Name: Cal. Ct. App.
# Author: Andrei Chelaru

from juriscraper.opinions.united_states_backscrapers.state import calctapp_1st


class Site(calctapp_1st.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.district = 43
        self.court_id = self.__module__
