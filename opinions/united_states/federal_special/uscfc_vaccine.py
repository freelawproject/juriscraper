"""Scraper for the United States Court of Federal Claims
CourtID: uscfc
Court Short Name: Fed. Cl."""

import uscfc

class Site(uscfc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = (
            'http://www.uscfc.uscourts.gov/opinions_decisions_vaccine/Published')
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for txt in self.html.xpath('//div[2]/table/tbody/tr/td[3]/a/text()'):        
            case_names.append(txt.strip()[:-8].replace('[', '').strip())
        return case_names