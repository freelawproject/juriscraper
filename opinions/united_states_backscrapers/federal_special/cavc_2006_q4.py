# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
from juriscraper.opinions.united_states.federal_special import cavc
from datetime import date
import time

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/Opinions20064thQuarter.cfm'
        self.court_id = self.__module__

    def _get_case_dates(self):
        dates = []
        for t in self.html.xpath('//table[1]/tbody/tr/td[1]/p/text()'):
            if t == u'\xa0':
                continue
            else:
                dates.append(date.fromtimestamp(time.mktime(time.strptime(t.strip(), '%d%b%y'))))
        return dates