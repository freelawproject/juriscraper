# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
import cavc
import time
import datetime
from datetime import date
from lxml import html

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/Opinions20033rdQuarter.cfm'
        self.court_id = self.__module__

    def _get_case_dates(self):
        dates = []
        # This page has one row with odd formatting that requires this:
        for e in self.html.xpath('//table[1]/tbody/tr[position() > 1]/td[1]/p'):
            s = html.tostring(e, method='text', encoding='unicode')
            # This page has a typo that we correct.            
            if s.strip() == '24SEP01':
                dates.append(datetime.date(2003, 9, 24))
            else:
                dates.append(date.fromtimestamp(time.mktime(time.strptime(
                    s.strip(), '%d%b%y'))))
        return dates

    def _get_case_names(self):
        case_names = []
        # This page has one row with odd formatting that requires this:
        for e in (self.html.xpath('//table[1]/tbody/tr[position() > 1]/td[3]/p')):
            s = html.tostring(e, method='text', encoding='unicode')            
            case_names.append(s + ' v. Principi')
        return case_names