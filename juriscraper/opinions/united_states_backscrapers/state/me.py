"""Backscraper for Supreme Court of Maine 2021 redux
CourtID: me
Court Short Name: Me.
Author: William E. Palin
Date created: March 31, 2021
"""

from juriscraper.opinions.united_states.state import me


class Site(me.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = [2020, 2019, 2018, 2017]

    def _download_backwards(self, year):
        self.url = f"https://www.courts.maine.gov/courts/sjc/lawcourt/{year}/index.html"
        self.html = self._download()
