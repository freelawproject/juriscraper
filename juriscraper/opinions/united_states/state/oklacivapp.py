# Scraper for Oklahoma Court of Civil Appeals
# CourtID: oklacivapp
# Court Short Name: OK
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05

from juriscraper.opinions.united_states.state import okla


class Site(okla.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.oscn.net/decisions/ok-civ-app/90"
