# Author: Michael Lissner
# Date created: 2013-06-11

import re
from datetime import date
from datetime import datetime

from juriscraper.GenericSite import GenericSite
from juriscraper.lib.string_utils import titlecase


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.sdjudicial.com/sc/scopinions.aspx'

    def _get_download_urls(self):
        path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]//a[2]/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]/td[2]/text()'
        case_names = []
        for s in self.html.xpath(path):
            case_name = re.search('(.*)(\d{4} S\.D\. \d{1,4})', s, re.MULTILINE).group(1)
            case_names.append(titlecase(case_name))
        return case_names

    def _get_case_dates(self):
        path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]/td[1]/@uv'
        return [datetime.strptime(date_string, '%m/%d/%Y').date()
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]//a[2]/@href'
        docket_numbers = []
        for url in self.html.xpath(path):
            docket_number = re.search('(\d+).pdf', url).group(1)
            docket_numbers.append(docket_number)
        return docket_numbers

    def _get_neutral_citations(self):
        path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]/td[2]/text()'
        neutral_cites = []
        for s in self.html.xpath(path):
            neutral_cite = re.search('(.*)(\d{4} S\.D\. \d{1,4})', s, re.MULTILINE).group(2)
            neutral_cites.append(titlecase(neutral_cite))
        return neutral_cites
