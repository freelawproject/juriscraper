# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
import cavc
from lxml import html

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/Opinions20113rdQuarter.cfm'
        self.court_id = self.__module__

    def _get_case_dates(self):
        dates = []
        for e in self.html.xpath('//table[1]/tbody/tr/td[1]'):
            s = html.tostring(e, method='text', encoding='unicode')
            dates.append(date.fromtimestamp(time.mktime(time.strptime(s, '%d%b%y'))))
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//table[1]/tbody/tr/td[2]'):
            s = html.tostring(e, method='text', encoding='unicode')
            docket_numbers.append(s)
        return docket_numbers
        
    def _get_download_urls(self):
        download_urls = []
        for e in self.html.xpath('//table[1]/tbody/tr/td[2]'):
            s = html.tostring(e, method='text', encoding='unicode')
            download_urls.append(s)
        return download_urls

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath('//table[1]/tbody/tr/td[3]'):
            s = html.tostring(e, method='text', encoding='unicode')
            # See https://en.wikipedia.org/wiki/United_States_Secretary_of_Veterans_Affairs
            # to know which name to append here for different opinion dates.
            # Jan. 20, 2009 to present is Shinseki.
            case_names.append(s + ' v. Shinseki')
        return case_names