# Backscraper Scraper for California's First District Court of Appeal
# CourtID: calctapp_1st
# Court Short Name: Cal. Ct. App.
# Author: Andrei Chelaru

from juriscraper.opinions.united_states_backscrapers.state import calctapp_1st


class Site(calctapp_1st.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.district = 2
        self.court_id = self.__module__
