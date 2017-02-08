# Scraper for California's Fourth District Court of Appeal Division 3
# CourtID: calctapp_4th_div3
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp_1st


class Site(calctapp_1st.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_code = 'G'
        self.division = '4th App. Dist. Div. 3'
