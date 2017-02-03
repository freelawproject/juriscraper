"""
Scraper for the Tennessee Court of Appeals
CourtID: tennctapp
Court Short Name: Tenn. Ct. App.
"""
from juriscraper.opinions.united_states.state import tenn


class Site(tenn.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.tsc.state.tn.us/courts/court-appeals/opinions'
        self.back_scrape_iterable = range(0, 987)
