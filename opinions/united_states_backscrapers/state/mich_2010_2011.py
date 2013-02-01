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
        for txt in self.html.xpath(
            "//table[4]/tr/td/table[4]/tr/td[1]/text()"):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(
                txt.strip(), '%m/%d/%y'))))
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        # A stray p tag makes this xpath complex.
        for txt in self.html.xpath(
            '//table[4]/tr/td/table[4]/tr/td[2]/text() | //table[4]/tr/td/table[4]/tr/td[2]/p/text()'):
            # Table has both a typo and problematic formatting corrected here.
            if txt == '140814':
                docket_numbers.append(
                '140814 140817 140818 140819 140820 140821 140822 140823 140824')
            elif 'and' in txt:
                continue
            elif '140817 to 14082' in txt:
                continue
            else:
                docket_numbers.append(txt)
        return docket_numbers

    def _get_case_names(self):
        case_names = []
        # Some stray p tags and span tags make this xpath complex.
        for txt in self.html.xpath(
            '//table[4]/tr/td/table[4]/tr/td[3]/a/text() | //table[4]/tr/td/table[4]/tr/td[3]/*/a/text()'):
            # One case name ignored because we get it under another name.
            if 'Iron Mountain v Naftaly' in txt:
                continue
            else:
                case_names.append(txt)
        return case_names

    def _get_download_urls(self):
        download_urls = []
        # Some stray p tags and span tags make this xpath complex.
        for txt in self.html.xpath(
            '//table[4]/tr/td/table[4]/tr/td[3]/a/@href | //table[4]/tr/td/table[4]/tr/td[3]/*/a/@href'):
            download_urls.append(txt)
        return download_urls

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)