"""Scraper for the Supreme Court of Michigan
CourtID: mich
Court Short Name: Mich.
Backscrapers possible back to 2007-08 term on this same page by parsing tables 
further down."""

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
            '//table[4]/tr/td/table[3]/tr/td[1]/text()'):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(
                txt.strip(), '%m/%d/%y'))))
        return dates

    def _get_docket_numbers(self):
        return [txt for txt in self.html.xpath(
            '//table[4]/tr/td/table[3]/tr/td[2]/text()')]

    def _get_case_names(self):
        case_names = []
        # Some stray p tags and span tags make this xpath complex.
        for txt in self.html.xpath(
            '//table[4]/tr/td/table[3]/tr/td[3]/a/text() | //table[4]/tr/td/table[3]/tr/td[3]/*/a/text()'):
            # Two case names ignored because we get them under other names.
            if 'People v King (Larry)' in txt:
                continue
            elif 'In Re J.L. Gordon, minor' in txt:
                continue
            else:
                case_names.append(txt)
        return case_names

    def _get_download_urls(self):
        download_urls = []
        # Some stray p tags and span tags make this xpath complex.
        for txt in self.html.xpath(
            '//table[4]/tr/td/table[3]/tr/td[3]/a/@href | //table[4]/tr/td/table[3]/tr/td[3]/*/a/@href'):
            # This table also includes a url from last year we must ignore.
            if '10-11-Term' in txt:
                continue
            else:
                download_urls.append(txt)
        # One url is listed 2x that shouldn't be and so 1 instance is removed.
        download_urls.remove(
'http://courts.michigan.gov/supremecourt/Clerk/11-12-Term-Opinions/142695.pdf')
        return download_urls

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)