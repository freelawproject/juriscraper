"""Scraper for the Supreme Court of Michigan
CourtID: mich
Court Short Name: Mich.
"""

from juriscraper.GenericSite import GenericSite
import time
from datetime import date

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = (
            'http://courts.michigan.gov/supremecourt/Clerk/Opinions.html')
        self.court_id = self.__module__

    def _get_case_dates(self):
        dates = []
        # Stray rows at the end lacking content require a precision xpath.
        for txt in self.html.xpath(
            '//table[4]/tr/td/table[5]/tr[position() > 1 and position() < 44]/td[1]/text()'):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(
                    txt.strip(), '%m/%d/%y'))))
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for txt in self.html.xpath(
            '//table[4]/tr/td/table[5]/tr/td[2]/text()'):
            # Improve one group of docket numbers.
            if '138456 to 138458' in txt:
                docket_numbers.append('138456 138457 138458')
            else:
                # Some minor docket number cleanup required.
                docket_numbers.append(txt.replace('-', ' ').replace(',', ''))
        return docket_numbers

    def _get_case_names(self):
        case_names = []
        for txt in self.html.xpath(
            '//table[4]/tr/td/table[5]/tr/td[3]/a/text()'):
            case_names.append(txt)
        return case_names

    def _get_download_urls(self):
        download_urls = []
        for txt in self.html.xpath(
            '//table[4]/tr/td/table[5]/tr/td[3]/a/@href'):
            download_urls.append(txt)
        return download_urls

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)