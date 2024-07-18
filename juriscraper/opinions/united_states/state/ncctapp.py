"""Scraper for North Carolina Court of Appeals
CourtID: ncctapp
Court Short Name: N.C. Ct. App.
Author: Jon Andersen
History:
    2014-08-04: Created by Jon Andersen
"""

from datetime import date

from juriscraper.opinions.united_states.state import nc


class Site(nc.Site):
    court = "coa"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
