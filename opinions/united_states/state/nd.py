# Author: Michael Lissner
# Date created: 2013-06-06

import re
from datetime import date
from datetime import datetime
from lxml import html

from juriscraper.GenericSite import GenericSite
# from juriscraper.lib.string_utils import titlecase


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        today = date.today()
        self.url = 'http://www.ndcourts.gov/opinions/month/%s.htm' % (today.strftime("%b%Y"))

    def _get_download_urls(self):
        path = '//a/@href'
        download_urls = []
        for html_link in self.html.xpath(path):
            case_number = re.search('(\d+)', html_link).group(0)
            download_urls.append('http://www.ndcourts.gov/wp/%s.wpd' % case_number)
        return download_urls

    def _get_case_names(self):
        path = '//a/text()'
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        # A tricky one. We get the case dates, but each can have different number of cases below it, so we have to
        # count them.
        case_dates = []
        path = '//body/a|//body/font'
        for e in self.html.xpath(path):
            if e.tag == 'font':
                date_str = e.text
                dt = datetime.strptime(date_str, '%B %d, %Y').date()
            elif e.tag == 'a':
                try:
                    case_dates.append(dt)
                except NameError:
                    # When we don't yet have the date
                    continue
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//a/@href'
        docket_numbers = []
        for html_link in self.html.xpath(path):
            docket_numbers.append(re.search('(\d+)', html_link).group(0))
        return docket_numbers

    def _get_neutral_citations(self):
        neutral_cites = []
        for t in self.html.xpath('//body/text()'):
            try:
                neutral_cites.append(re.search('(\d{4} ND \d{1,4})', t).group(0))
            except AttributeError:
                continue
        return neutral_cites

    def _download_backwards(self, d):
        self.url = 'http://www.ndcourts.gov/opinions/month/%s.htm' % (d.strftime("%b%Y"))
        self.html = self._download()
