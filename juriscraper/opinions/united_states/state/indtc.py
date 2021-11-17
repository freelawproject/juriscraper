"""
Scraper for Indiana Tax Court
CourtID: indtc
Court Short Name: Ind. Tax.
Auth: Jon Andersen <janderse@gmail.com>
Reviewer: mlr
History:
    2014-09-03: Created by Jon Andersen
"""
from juriscraper.opinions.united_states.state import ind


class Site(ind.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.in.gov/judiciary/opinions/taxcourt.html"
