# Scraper for California's First District Court of Appeal
# CourtID: calctapp_1st
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import cal


class Site(cal.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_code = "A"
        self.division = "1st App. Dist."
        self.url = self.build_url()

    def _get_divisions(self):
        return [self.division] * len(self.case_names)
