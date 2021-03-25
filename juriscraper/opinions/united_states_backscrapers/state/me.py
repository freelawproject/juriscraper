"""Backscraper for Supreme Court of Maine 2017+
CourtID: me
Court Short Name: Me.
Author: William Palin
Date created: March 25, 2021
"""

from juriscraper.opinions.united_states.state import me


class Site(me.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__

    def backscrape_year(self, year):
        self.url = f"https://www.courts.maine.gov/courts/sjc/lawcourt/{year}/index.html"
