# Author: Krist Jin
# Reviewer: Michael Lissner
# Date created: 2013-08-03
import re
from lxml import html

import time
from datetime import date
from datetime import datetime

from juriscraper.GenericSite import GenericSite
from juriscraper.lib.string_utils import titlecase


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.judiciary.state.nj.us/opinions/index.htm'
        self.table = '1'  # Used as part of the paths to differentiate between appellate and supreme

    def _get_download_urls(self):
        path = '//*[@id="content2col"]/table[%s]/tr/td[3]//a/@href' % self.table
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//*[@id="content2col"]/table[%s]/tr/td[3]//a/text()[1]' % self.table
        return [titlecase(t.upper()) for t in self.html.xpath(path)]

    def _get_case_dates(self):
        dates = []
        path = ('//*[@id="content2col"]/table[%s]/tr'
                '[not(contains(., "No Appellate opinions approved for publication."))]'
                '[not(contains(., "No Supreme Court opinions reported"))]'
                '/td[1]//text()' % self.table)
        for s in self.html.xpath(path):
            s = s.strip()
            s = re.sub('[\.,]', '', s)
            s = s.replace('Sept', 'Sep')
            date_formats = ['%b %d %Y', '%B %d %Y']
            for format in date_formats:
                try:
                    dates.append(date.fromtimestamp(time.mktime(time.strptime(s, format))))
                    # This break is necessary for a funny reason. 11 months out of the year, only one of the
                    # date_formats will match and things will work smoothly. In May, however, %b == 'May' as
                    # does %B. When that happens, both date formats match, and you get double metadata. This
                    # break takes us out of this inner for loop as soon as we have a match, so the next
                    # format can't be attempted. Yikes, dates always have one more tricky thing.
                    break
                except ValueError:
                    pass
        return dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        path = ('//*[@id="content2col"]/table[%s]/tr'
                '[not(contains(., "No Appellate opinions approved for publication."))]'
                '[not(contains(., "No Supreme Court opinions reported"))]'
                '/td[2]' % self.table)
        docket_numbers = []
        for cell in self.html.xpath(path):
            docket_numbers.append(html.tostring(cell, method='text', encoding='unicode'))
        return docket_numbers
