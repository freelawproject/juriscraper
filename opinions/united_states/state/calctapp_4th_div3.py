# Scraper for California's Fourth District Court of Appeal Division 3
# CourtID: calctapp_4th_div3
# Court Short Name: Cal. Ct. App.
from juriscraper.opinions.united_states.state import cal


class Site(cal.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.courtinfo.ca.gov/cgi-bin/opinions-blank.cgi?Courts=G'
        self.court_id = self.__module__

    def _get_divisions(self):
        return ['4th App. Dist. Div. 3'] * len(self.case_names)
