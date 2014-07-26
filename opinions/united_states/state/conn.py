"""Scraper for Connecticut Supreme Court
CourtID: conn
Court Short Name: Conn.
Author: Asadullah Baig<asadullahbeg@outlook.com>

Date created: 2014-07-11
"""

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import clean_string
from datetime import date, datetime
import re


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.crawl_date = date.today()
        self.url = 'http://www.jud.ct.gov/external/supapp/archiveAROsup{year}.htm'.format(
            year=self.crawl_date.strftime("%y"))
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        path = '//*[@id="AutoNumber1"]/tr[2]/td/table/tr/td//ul//text()'
        for s in self.html.xpath(path):
            if '-' in s:
                case_names.append(clean_string(s))
        return case_names

    def _get_download_urls(self):
        return list(self.html.xpath('//@href[contains(., ".pdf")]'))

    def _get_case_dates(self):
        dates = []
        for title in self.html.xpath('//table[@id="AutoNumber1"]/tr[2]/td/table/tr/td/p//text()'):
            count = len(title.getparent().xpath("following::ul[1]//a/@href[contains(., 'pdf')]"))
            date_string = title.split()[-1].strip(':')
            dates.extend([datetime.strptime(date_string, '%m/%d/%y').date()] * count)
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for d in self.html.xpath("//a[contains(./@href, '.pdf')]/text()"):
            if re.search(r"(A?S?C\d{3,5})", d):
                docket_numbers.append(d)
        return docket_numbers

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)
