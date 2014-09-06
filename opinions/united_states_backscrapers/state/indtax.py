"""
Backscraper for Indiana Tax Court
CourtID: indtax
Court Short Name: Ind. Tax.
Auth: Jon Andersen <janderse@gmail.com>
Reviewer:
History:
    2014-09-03: Created by Jon Andersen
"""
from juriscraper.OpinionSite import OpinionSite
from juriscraper.opinions.united_states_backscrapers.state import ind


class Site(ind.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.in.gov/judiciary/opinions/archtax.html'
