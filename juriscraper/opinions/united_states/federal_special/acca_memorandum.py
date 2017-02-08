"""Scraper for Army Court of Criminal Appeals
CourtID: acca
Reviewer: None
History:
  2015-01-08: Created by mlr
"""

from juriscraper.opinions.united_states.federal_special import acca_p


class Site(acca_p.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'https://www.jagcnet.army.mil/85257546006DF36B/MODD?OpenView&Count=-1'
        self.court_id = self.__module__

    def _get_precedential_statuses(self):
        return ['Unpublished'] * len(self.case_names)
