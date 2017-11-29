#  Scraper for Pennsylvania Supreme Court
# CourtID: pasup
# Court Short Name: pasup
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 21 July 2014

from juriscraper.opinions.united_states.state import pa
import re


class Site(pa.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.pacourts.us/assets/rss/SuperiorOpinionsRss.ashx"

    def _get_judges(self):
        # Judges for this feed are provided as obscure numbers.
        return None
