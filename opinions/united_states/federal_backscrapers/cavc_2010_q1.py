# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
import cavc

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/Opinions20101stQuarter.cfm'
        self.court_id = self.__module__

    def _get_docket_numbers(self):
        docket_numbers = []
        for t in self.html.xpath('//table[1]/tbody/tr/td[2]/p/a/text()'):
            docket_numbers.append(t)
        # This column of last row has extraneous tags:
        for t in self.html.xpath('//table[1]/tbody/tr/font/strong/td/p/a/text()'):
            docket_numbers.append(t)
        return docket_numbers
    
    def _get_download_urls(self):
        download_urls = []        
        for t in self.html.xpath('//table[1]/tbody/tr/td[2]/p/a/@href'):
            download_urls.append(t)
        # This column of last row has extraneous tags:
        for t in self.html.xpath('//table[1]/tbody/tr/font/strong/td/p/a/@href'):
            download_urls.append(t)
        return download_urls

    def _get_case_names(self):
        case_names = []
        for t in self.html.xpath('//table[1]/tbody/tr/td[3]/p/text()'):
            # See https://en.wikipedia.org/wiki/United_States_Secretary_of_Veterans_Affairs
            # to know which name to append here for different opinion dates.
            # Jan. 20, 2009 to present is Shinseki.
            case_names.append(t + ' v. Shinseki')
        # This column of last row has extraneous tags:        
        for t in self.html.xpath('//table[1]/tbody/tr/font/strong/td/p/text()'):
            case_names.append(t + ' v. Shinseki')
        return case_names
