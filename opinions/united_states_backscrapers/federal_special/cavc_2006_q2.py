# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
from juriscraper.opinions.united_states.federal_special import cavc
import datetime
from datetime import date
import time
from lxml import html

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/Opinions20062ndQuarter.cfm'
        self.court_id = self.__module__

    def _get_case_dates(self):
        dates = []
        for t in self.html.xpath('//table[1]/tbody/tr/td[1]/p/text()'):
            # This page has a typo that we correct.            
            if t == '04APR07':
                dates.append(datetime.date(2006, 4, 4))
            else:
                dates.append(date.fromtimestamp(time.mktime(time.strptime(t.strip(), '%d%b%y'))))
        return dates

    def _get_case_names(self):
        case_names = []
        # This page has one row with odd formatting that requires this:
        for e in self.html.xpath('//table[1]/tbody/tr[position() > 1]/td[3]/p'):
            s = html.tostring(e, method='text', encoding='unicode')
            case_names.append(s + ' v. Nicholson')
        return case_names