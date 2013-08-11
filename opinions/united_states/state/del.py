"""Scraper for the Supreme Court of Delaware
CourtID: del
Court Short Name: Del.
"""

from juriscraper.GenericSite import GenericSite
import time
from datetime import date

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://courts.delaware.gov/opinions/list.aspx?ag=supreme%20court'
        self.court_id = self.__module__

    def _get_case_dates(self):
        case_dates = []
        for t in self.html.xpath('//table/tr/td[1]/text()'):
            case_dates.append(date.fromtimestamp(time.mktime(time.strptime(t, '%m/%d/%Y'))))
        return case_dates

    def _get_download_urls(self):
        return [t for t in self.html.xpath('//table/tr/td[2]/strong/a/@href')]

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath('//table/tr/td[2]/strong/a'):
            s = html.tostring (e, method='text', encoding='unicode').strip()
            case_names.append(s.strip())
        return case_names

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//table/tr[position() > 2 and position() < 53]/td[3]'):
            s = html.tostring (e, method='text', encoding='unicode').strip()
            docket_numbers.append(s.replace('\r\n', ' &'))
        return docket_numbers

# Because there are sometimes multiple judges we have to strip some whitespace.
    def _get_judges(self):
        judges = []
        for e in self.html.xpath('//table/tr[position() > 2 and position() < 53]/td[5]'):
            s = html.tostring (e, method='text', encoding='unicode')
            judges.append(s.strip())
        return judges