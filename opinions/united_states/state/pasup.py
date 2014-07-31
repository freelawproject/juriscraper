#  Scraper for Pennsylvania Supreme Court
# CourtID: pasup
# Court Short Name: pasup
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 21 July 2014

from juriscraper.opinions.united_states.state import pa


class Site(pa.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = "http://www.pacourts.us/assets/rss/SuperiorOpinionsRss.ashx"

    def _get_judges(self):
        # Judges for this feed are provided as obscure numbers.
        return None
