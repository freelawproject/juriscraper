"""Scraper for the United States Court of Federal Claims
CourtID: uscfc
Court Short Name: Fed. Cl."""

import uscfc
from juriscraper.lib.string_utils import titlecase


class Site(uscfc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscfc.uscourts.gov/opinions_decisions_general/Unpublished'
        self.court_id = self.__module__

    def _get_precedential_statuses(self):
        return ['Unpublished'] * len(self.case_names)

    def _get_summaries(self):
        summaries = []
        for txt in self.html.xpath('//div[2]/table/tbody/tr/td[4]/a/text()'):
            summaries.append(titlecase(txt.lower()))
        return summaries
