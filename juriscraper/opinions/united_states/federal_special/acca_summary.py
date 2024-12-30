"""Scraper for Army Court of Criminal Appeals
CourtID: acca
Reviewer: None
History:
  2015-01-08: Created by mlr
"""

from juriscraper.opinions.united_states.federal_special import acca_p


class Site(acca_p.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.jagcnet.army.mil/ACCALibrary/cases/opinions/SD"
        self.court_id = self.__module__
        self.status = "Unpublished"
