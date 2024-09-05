# Scraper for New York Appellate Divisions 1st Dept.
# CourtID: nyappdiv_1st
# Court Short Name: NY
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-04
import re
from datetime import date

from juriscraper.opinions.united_states.state import ny
from juriscraper.OpinionSite import OpinionSite


class Site(ny.Site):
    first_opinion_date = date(2003, 9, 25)
    ny.Site.extract_from_text = OpinionSite.extract_from_text

    # If more than 500 results are found, no results will be shown
    days_interval = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "App Div, 1st Dept"
        self._set_parameters()
        self.make_backscrape_iterable(kwargs)
