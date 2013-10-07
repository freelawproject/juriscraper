"""
Scraper for the Tennessee Court of Criminal Appeals
CourtID: tennctcrimapp
Court Short Name: Tenn. Ct. Crim. App.
"""
import tenn

class Site(tenn.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.tsc.state.tn.us/courts/court-criminal-appeals/opinions'