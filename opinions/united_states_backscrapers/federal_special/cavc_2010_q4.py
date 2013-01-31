# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
from juriscraper.opinions.united_states.federal_special import cavc

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/Opinions20104thQuarter.cfm'
        self.court_id = self.__module__
    
    def _get_download_urls(self):
        download_urls = []
        for url in self.html.xpath('//table[1]/tbody/tr/td[2]/p/a/@href'):
            if url == 'http://www.uscourts.cavc.gov/orders_and_opinions/documents/Cogburn_08-1561_published_opinion_12-13-2010.pdf':
                download_urls.append('http://www.uscourts.cavc.gov/documents/Cogburn_08-1561_published_opinion_12-13-2010.pdf')
            else:
                download_urls.append(url)
        return download_urls