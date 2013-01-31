# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
from juriscraper.opinions.united_states.federal_special import cavc
from lxml import html

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/2002FullCourtOrders.cfm'
        self.court_id = self.__module__

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//table[1]/tbody/tr/td[2]/p/a'):
            s = html.tostring(e, method='text', encoding='unicode')
            docket_numbers.append(s.replace('/',''))
        return docket_numbers