# Scraper for California's Second District Court of Appeal
# CourtID: calctapp_2nd
# Court Short Name: Cal. Ct. App.
from juriscraper.opinions.united_states.state import cal


class Site(cal.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.courtinfo.ca.gov/cgi-bin/opinions-blank.cgi?Courts=B'
        self.court_id = self.__module__

    def _get_divisions(self):
        return ['2nd App. Dist.'] * len(self.case_names)
