"""Scraper for the Supreme Court of Vermont
CourtID: vt
Court Short Name: VT
Author: Brian W. Carver
Date created: 18 Aug 2013
Reviewer: Mike Lissner
"""

import re
from datetime import date
from datetime import datetime
from lxml import html

from juriscraper.GenericSite import GenericSite


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://info.libraries.vermont.gov/supct/op.html'

    def _get_download_urls(self):
        path = '//h4/a/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        case_names = []
        path = "//h4/a"
        for e in self.html.xpath(path):
            s = html.tostring(e, method='text', encoding='unicode')
            expression = '(^[^\(]*)'  # Start of line and all characters until '('
            case_name = re.search(expression, s, re.MULTILINE).group(1)
            case_names.append(case_name)
        return case_names

    def _get_case_dates(self):
        case_dates = []
        path = '//h4/a'
        for e in self.html.xpath(path):
            s = html.tostring(e, method='text', encoding='unicode')
            expression = '(\d+-\w{3}-\d{4})'
            date_string = re.search(expression, s, re.MULTILINE).group(1)
            case_dates.append(datetime.strptime(date_string, '%d-%b-%Y').date())
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_numbers = []
        path = '//h4/a'
        for e in self.html.xpath(path):
            s = ' '.join(html.tostring(e, method='text', encoding='unicode').split())
            regexes = ['(\d{4}-\d{2,3} \& \d{4}-\d{2,3})', '(\d{4}-\d{2,3})']
            for regex in regexes:
                try:
                    docket_number = re.search(regex, s).group(1)
                    break
                except AttributeError:
                    # Happens when a regex doesn't match.
                    continue
            docket_numbers.append(docket_number)
        return docket_numbers
