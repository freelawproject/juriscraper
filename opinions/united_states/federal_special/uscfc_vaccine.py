"""Scraper for the United States Court of Federal Claims
CourtID: uscfc
Court Short Name: Fed. Cl."""

import uscfc
from juriscraper.lib.string_utils import harmonize, titlecase

class Site(uscfc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = (
            'http://www.uscfc.uscourts.gov/opinions_decisions_vaccine/Published')
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for txt in self.html.xpath('//div[2]/table/tbody/tr/td[3]/a/text()'):
            case_name = txt.strip()[:-8].replace('[', '')
            case_name = titlecase(case_name.lower())
            case_names.append(case_name)
        return case_names
