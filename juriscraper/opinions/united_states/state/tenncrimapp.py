"""
Scraper for the Tennessee Court of Criminal Appeals
CourtID: tennctcrimapp
Court Short Name: Tenn. Ct. Crim. App.
"""

from juriscraper.opinions.united_states.state import tenn


class Site(tenn.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.tncourts.gov/courts/court-criminal-appeals/opinions"
        )
