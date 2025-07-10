"""
Scraper for Indiana Court of Appeals
CourtID: indctapp
Court Short Name: Ind. Ct. App.
Auth: Jon Andersen <janderse@gmail.com>
Reviewer: mlr
History:
    2014-09-03: Created by Jon Andersen
"""

from juriscraper.opinions.united_states.state import ind


class Site(ind.Site):
    page_court_id = "9530"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "Court of Appeals"
