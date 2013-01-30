# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
import cavc
from lxml import html

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/Opinions20053rdQuarter.cfm'
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        # This page has one row with odd formatting that requires this:
        for e in self.html.xpath('//table[1]/tbody/tr[position() > 1]/td[3]/p'):
            s = html.tostring(e, method='text', encoding='unicode')
            case_names.append(s + ' v. Nicholson')
        return case_names