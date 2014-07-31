"""Scraper for the Supreme Court of Delaware
CourtID: del

Creator: Andrei Chelaru
Reviewer: mlr
"""

import re
import time
from datetime import date

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://courts.delaware.gov/opinions/list.aspx?ag=supreme%20court'
        self.court_id = self.__module__
        self.base_path = "//*[contains(concat(' ',@class,' '),'Row')]/td[6][contains(., 'Opinion')]/preceding::"

    def _clean_text(self, text):
        text = re.sub(r'<!\[CDATA\[', '', text)
        text = re.sub(r'\]\]>', '', text)
        if isinstance(text, unicode):
            text = re.sub(r'^\s*<\?xml\s+.*?\?>', '', text)
        text = re.sub('</br>', '<br/>', text)
        #text = ''.join(c for c in text if self.valid_XML_char_ordinal(ord(c)))
        return text

    def valid_XML_char_ordinal(self, i):
        # http://stackoverflow.com/questions/8733233/filtering-out-certain-bytes-in-python
        return (# conditions ordered by presumed frequency
            0x20 <= i <= 0xD7FF
            or i in (0x9, 0xA, 0xD)
            or 0xE000 <= i <= 0xFFFD
            or 0x10000 <= i <= 0x10FFFF
            )

    def _get_case_dates(self):
        path = "{base}td[5]/text()".format(base=self.base_path)
        case_dates = []
        for t in self.html.xpath(path):
            case_dates.append(date.fromtimestamp(time.mktime(time.strptime(t, '%m/%d/%y'))))
        return case_dates

    def _get_download_urls(self):
        path = "{base}td[4]//a/@href[not(contains(., 'mailto'))]".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = "{base}td[4]//a[not(contains(./@href, 'mailto'))]/text()[1]".format(base=self.base_path)
        return [case_name.strip() for case_name in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = "{base}td[3]".format(base=self.base_path)
        docket_numbers = []
        for e in self.html.xpath(path):
            text = ' '.join(e.xpath('./text()'))
            docket_numbers.append(text)
        return docket_numbers

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)

    def _get_judges(self):
        path = "{base}td[1]/text()[1]".format(base=self.base_path)
        return [judge.strip() for judge in self.html.xpath(path)]
