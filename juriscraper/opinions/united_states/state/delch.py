#  Scraper for the Court Of Chancery of Delaware
# CourtID: dechan
# Court Short Name: De.
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 31 July 2014

from juriscraper.OpinionSite import OpinionSite
from juriscraper.opinions.united_states.state import delaware


class Site(delaware.Site):
    extract_from_text = OpinionSite.extract_from_text

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://courts.delaware.gov/opinions/List.aspx?ag=Court%20of%20Chancery"
        self.court_id = self.__module__
