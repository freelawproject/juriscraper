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
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.in.gov/judiciary/opinions/appeals.html'
