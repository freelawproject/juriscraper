#  Scraper for the Superior Court of Delaware
# CourtID: desup
# Court Short Name: De.
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 31 July 2014

from juriscraper.opinions.united_states.state import delaware
from juriscraper.OpinionSite import OpinionSite


class Site(delaware.Site):
    extract_from_text = OpinionSite.extract_from_text

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://courts.delaware.gov/opinions/List.aspx?ag=Superior%20Court"
        self.court_id = self.__module__
