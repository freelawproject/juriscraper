# Scraper for California's Superior Court Appellate Division
# CourtID: calctapp_app_div
# Court Short Name: Cal. Ct. App.
from juriscraper.opinions.united_states.state import cal


class Site(cal.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.courtinfo.ca.gov/cgi-bin/opinions-blank.cgi?Courts=J'
        self.court_id = self.__module__

    def _get_divisions(self):
        return ['App. Div.'] * len(self.case_names)
