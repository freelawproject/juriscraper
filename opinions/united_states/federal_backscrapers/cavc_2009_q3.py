# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
import cavc
from lxml import html

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/Opinions20093rdQuarter.cfm'
        self.court_id = self.__module__

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//table[1]/tbody/tr/td[2]/p/a'):
            s = html.tostring(e, method='text', encoding='unicode')
            # Two documents have multiple docket numbers that are misbehaving.
            # This is an ugly hack that works.
            if s == '07-8003& 07-8007':
                docket_numbers.append('07-8003 07-8007')
            elif s == '08-1169704-2375(E)':
                docket_numbers.append('08-11697 04-2375(E)')
            else:
                docket_numbers.append(s)    
        return docket_numbers