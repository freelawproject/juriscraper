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
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/Opinions20003rdQuarter.cfm'
        self.court_id = self.__module__

    def _get_case_dates(self):
        dates = []
        # This page has one row with odd formatting that requires this:
        for e in self.html.xpath('//table[1]/tbody/tr[position() > 1]/td[1]/p'):
            s = html.tostring(e, method='text', encoding='unicode')
            dates.append(date.fromtimestamp(time.mktime(time.strptime(
                s.strip(), '%d%b%y'))))
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for t in self.html.xpath('//table[1]/tbody/tr/td[2]/p/a/text()'):
            if 'Quarter' in t:
                continue
            else:
                docket_numbers.append(t)
        return docket_numbers
    
    def _get_download_urls(self):
        download_urls = []
        for t in self.html.xpath('//table[1]/tbody/tr/td[2]/p/a/@href'):
            if 'Quarter' in t:
                continue
            else:
                download_urls.append(t)
        return download_urls