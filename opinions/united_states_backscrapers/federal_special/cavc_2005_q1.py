# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
from juriscraper.opinions.united_states.federal_special import cavc
import time
import datetime
from datetime import date
from lxml import html

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/Opinions20051stQuarter.cfm'
        self.court_id = self.__module__

    def _get_case_dates(self):
        dates = []
        # This page has one row with odd formatting that requires this:
        for e in self.html.xpath('//table[1]/tbody/tr[position() > 1]/td[1]/p'):
            s = html.tostring(e, method='text', encoding='unicode')
            dates.append(date.fromtimestamp(time.mktime(time.strptime(
                s.strip(), '%d%b%y'))))
        return dates

    def _get_case_names(self):
        case_names = []
        # This page has one row with odd formatting that requires this:
        dates = self._get_case_dates()
        for e, d in zip(self.html.xpath('//table[1]/tbody/tr[position() > 1]/td[3]/p'), dates):
            s = html.tostring(e, method='text', encoding='unicode')            
            if d > datetime.date(2005, 1, 26):
                case_names.append(s + ' v. Nicholson')
            else:
                case_names.append(s + ' v. Principi')
        return case_names