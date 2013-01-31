# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
from juriscraper.opinions.united_states.federal_special import cavc

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/Opinions20114thQuarter.cfm'
        self.court_id = self.__module__

    def _get_docket_numbers(self):
        docket_numbers = []
        for t in self.html.xpath('//table[1]/tbody/tr/td[2]/p/a/text()'):
            if t == '09-3758':
                continue
            elif t == '10-2139':
                continue
            elif t == '10-2622':
                continue
            elif t == '08-1468':
                docket_numbers.append('08-1468 09-3758 10-2139 10-2622')
            else:
                docket_numbers.append(t)
        return docket_numbers

    def _get_case_names(self):
        case_names = []
        for t in self.html.xpath('//table[1]/tbody/tr/td[3]/p/text()'):
            # See https://en.wikipedia.org/wiki/United_States_Secretary_of_Veterans_Affairs
            # to know which name to append here for different opinion dates.
            # Jan. 20, 2009 to present is Shinseki.
            if t == 'Rasheed':
                continue
            elif t == 'Lopez':
                continue
            elif t == 'King':
                continue
            else:
                case_names.append(t + ' v. Shinseki')
        return case_names