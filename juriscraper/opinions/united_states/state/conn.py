# coding=utf-8
"""Scraper for Connecticut Supreme Court
CourtID: conn
Court Short Name: Conn.
Author: Asadullah Baig <asadullahbeg@outlook.com>

History:
 - 2014-07-11: created
 - 2014-08-08, mlr: updated to fix InsanityError on case_dates
 - 2014-09-18, mlr: updated XPath to fix InsanityError on docket_numbers
 - 2015-06-17, mlr: made it more lenient about date formatting
 - 2016-07-21, arderyp: fixed to handle altered site format
"""

import re
from datetime import date

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import clean_string
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.crawl_date = date.today()
        self.url = 'http://www.jud.ct.gov/external/supapp/archiveAROsup{year}.htm'.format(
            year=self.crawl_date.strftime("%y"))
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        path = '//*[@id="AutoNumber1"]/tr[2]/td/table/tr/td//ul//text()'
        for text in self.html.xpath(path):
            if re.search(u'[–-]', text):
                case_names.append(clean_string(text))
        return case_names

    def _get_download_urls(self):
        return list(self.html.xpath('//@href[contains(., ".pdf")]'))

    def _get_case_dates(self):
        dates = []
        target_cell = self.html.xpath('//table[@id="AutoNumber1"]/tr[2]/td/table/tr/td')[0]
        for text in target_cell.xpath('//b//text() | //strong//text()'):
            text_clean = clean_string(text)
            if text_clean:
                last_substring = text_clean.split()[-1]
                if last_substring.endswith(':') and last_substring.count('/') == 2:
                    date = convert_date_string(last_substring.rstrip(':'))
                    count = len(text.getparent().xpath("following::ul[1]//a/@href[contains(., 'pdf')]"))
                    dates.extend([date] * count)
        return dates

    def _get_docket_numbers(self):
        dockets = []
        for text in self.html.xpath("//a[contains(./@href, '.pdf')]//text()"):
            if re.search(r"(A?S?C\d{3,5})", text):
                docket = text.strip('Dissent').strip('Concurrence').strip()
                dockets.append(docket)
        return dockets

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)
