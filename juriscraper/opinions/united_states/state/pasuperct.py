"""
Scraper for Pennsylvania Superior Court
CourtID: pasup
Court Short Name: pasup
Author: Andrei Chelaru
Reviewer: mlr
Date created: 21 July 2014
"""

from juriscraper.opinions.united_states.state import pa


class Site(pa.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.pacourts.us/Rss/Opinions/Superior/"

    def _get_precedential_statuses(self):
        """Mark superior court opinions Unpublished

        :return: List of published statuses
        """
        return ["Unpublished"] * len(self.cases)
