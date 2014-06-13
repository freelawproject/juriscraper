"""Scraper for North Carolina Supreme Court
CourtID: [unique abbreviation to be used by software/filesystem]
Court Short Name: nc
Author: Brian Carver
Date created: May 1 2014
"""

import re
from datetime import date
from datetime import datetime

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://appellate.nccourts.org/opinions/?c=sc&year=%s' % 2013 #date.today().year

    def _get_download_urls(self):
        urls = []
        path = "//table[2]//tr/td/span/span[1]/@onclick"
        # Have to trim these to remove 13 characters from the beginning and
        # 2 characters from the end of the string to get the bare URL
        for txt in self.html.xpath(path):
            urls.append(txt[13:-2])
        return urls

    def _get_case_names(self):
        case_names = []
        path = "//table[2]//tr/td/span/span[contains(@class,'title')]/text()"
        for txt in self.html.xpath(path):
            case_name = txt.rsplit('(')[0].strip()
            case_names.append(case_name)
        return case_names

    def _get_case_dates(self):
        case_dates = []
        date_cleaner = "\d* .* 20\d\d"
        date_str = None
        path = '//table[2]//tr'
        for row_el in self.html.xpath(path):
            # Examine each row. If it contains the date, we set that as the current date. If it contains a case, we
            # append the date once to our case_date list.
            try:
                date_nodes = row_el.xpath('.//strong/text()')
                date_str = date_nodes[0]
            except IndexError:
                # No match
                pass
            is_case_row = row_el.xpath('self::tr[@class = "hover"]')
            if date_nodes:
                date_str = re.search(date_cleaner, date_str, re.MULTILINE).group()
            elif is_case_row:
                case_dates.append(datetime.strptime(date_str, '%d %B %Y').date())
            else:
                # Some junk we don't care about
                continue

        return case_dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_nums = []
        path = "//table[2]//tr/td/span/span[contains(@class,'title')]/text()"
        for txt in self.html.xpath(path):
            docket_num = txt.rsplit('(')[1].strip().strip(')')
            docket_nums.append(docket_num)
        return docket_nums

    def _get_summaries(self):
        summaries = []
        path = "//table[2]//tr/td/span/span[contains(@class,'desc')]/text()"
        for txt in self.html.xpath(path):
            summaries.append(txt)
        return summaries

    def _download_backwards(self, year):
        self.url = 'http://appellate.nccourts.org/opinions/?c=sc&year=%s' % year
        self.html = self._download()
