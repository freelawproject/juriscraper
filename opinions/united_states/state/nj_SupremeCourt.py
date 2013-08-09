# Author: Krist Jin
# Date created: 2013-08-03

import re
import time
from datetime import date
from datetime import datetime
from lxml import html

from juriscraper.GenericSite import GenericSite
from juriscraper.lib.string_utils import titlecase


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.judiciary.state.nj.us/opinions/index.htm'

    def _get_download_urls(self):
        path = '//*[@id="content2col"]/table[1]/tr/td[3]/a/@href'
        return ["http://www.judiciary.state.nj.us/opinions/"+t for t in self.html.xpath(path)]

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath('//*[@id="content2col"]/table[1]/tr/td[3]/a/text()[1]'):
            e.strip()
            case_names.append(titlecase(e))
        return case_names

    def _get_case_dates(self):
        dates = []
        for s in self.html.xpath('//*[@id="content2col"]/table[1]/tr[not(contains(., "No Supreme Court opinions reported."))]/td[1]//text()'):
            s = s.strip()
            s = s.replace('.','')
            date_formats = ['%b %d, %Y', '%B %d, %Y']
            for format in date_formats:
                try:
                    dates.append(date.fromtimestamp(time.mktime(time.strptime(s, format))))
                except ValueError:
                    pass
        return dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//*[@id="content2col"]/table[1]/tr[not(contains(., "No Supreme Court opinions reported."))]/td[2]//text()'
        return [t for t in self.html.xpath(path)]
