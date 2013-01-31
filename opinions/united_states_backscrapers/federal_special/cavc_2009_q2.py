# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
from juriscraper.opinions.united_states.federal_special import cavc
from lxml import html

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/Opinions20092ndQuarter.cfm'
        self.court_id = self.__module__

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//table[1]/tbody/tr/td[2]/p/a'):
            s = html.tostring(e, method='text', encoding='unicode')
            # Five documents have multiple docket numbers that are misbehaving.
            # This is an ugly hack that works.
            if s == '01-0945(E)08-11370':
                docket_numbers.append('01-0945(E) 08-11370')
            elif s == '08-1126705-3204(E)':
                docket_numbers.append('08-11267 05-3204(E)')
            elif s == '04-2310& 06-1546':
                docket_numbers.append('04-2310 06-1546')
            elif s == '01-1965& 03-1717':
                docket_numbers.append('01-1965 03-1717')
            elif s == '08-1005204-1254(E)':
                docket_numbers.append('08-10052 04-1254(E)')
            else:
                docket_numbers.append(s)    
        return docket_numbers

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath('//table[1]/tbody/tr/td[3]/p'):
            s = html.tostring(e, method='text', encoding='unicode')
            if s == 'Jackson& Kelly':
                case_names.append('Jackson v. Shinseki')
            # See https://en.wikipedia.org/wiki/United_States_Secretary_of_Veterans_Affairs
            # to know which name to append here for different opinion dates.
            # Jan. 20, 2009 to present is Shinseki.
            else:
                case_names.append(s + ' v. Shinseki')
        return case_names