"""Scraper for Missouri Western Appellate District
CourtID: moctapp_western
Court Short Name: MO
Author: Ben Cassedy
Date created: 04/27/2014
History:
    - 2022-02-04, satsuki-chan: Fixed error when not found judge and disposition, changed super class to OpinionSiteLinear
"""

from juriscraper.opinions.united_states.state import mo


class Site(mo.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_slug = "Western"
        self.url = self.build_url()
        self.division = "Western Dist."
