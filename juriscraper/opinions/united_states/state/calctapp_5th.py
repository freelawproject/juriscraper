# Scraper for California's Fifth District Court of Appeal
# CourtID: calctapp_5th
# Court Short Name: Cal. Ct. App.
from juriscraper.opinions.united_states.state import cal


class Site(cal.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.courtinfo.ca.gov/cgi-bin/opinions-blank.cgi?Courts=F'
        self.court_id = self.__module__

    def _get_divisions(self):
        return ['5th App. Dist.'] * len(self.case_names)
