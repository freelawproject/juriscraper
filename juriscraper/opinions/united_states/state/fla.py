# Scraper for Florida Supreme Court
# CourtID: fla
# Court Short Name: fla
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 21 July 2014

import re
from lxml import html
from datetime import date

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string



class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = date.today().year
        self.regex = re.compile("(S?C\d+-\d+)(.*)")
        self.base_path = "//h2[contains(., '{y}')]".format(y=self.year)
        self.back_scrape_iterable = range(1999, 2013)
        self.url = 'http://www.floridasupremecourt.org/decisions/opinions.shtml'

    def _get_case_names(self):
        path = '{base}/text()/following::ul[1]//li' \
               '//a[not(contains(., "Notice"))][not(contains(., "Rehearing Order"))]'.format(
            base=self.base_path)
        case_names = []
        for e in self.html.xpath(path):
            s = ' '.join(e.xpath('.//text()'))
            try:
                case_name = self.regex.search(s).group(2)
                if not case_name.strip():
                    continue
                else:
                    case_names.append(case_name)
            except AttributeError:
                pass
        return case_names

    def _get_download_urls(self):
        path = '{base}/text()/following::ul[1]//li' \
               '//a[not(contains(., "Notice"))][not(contains(., "Rehearing Order"))]'.format(
            base=self.base_path)
        urls = []
        for e in self.html.xpath(path):
            try:
                case_name_check = self.regex.search(html.tostring(e, method='text', encoding='unicode')).group(2)
                if not case_name_check.strip():
                    continue
                else:
                    urls.append(e.xpath('@href')[0])
            except AttributeError:
                pass
        return urls

    def _get_case_dates(self):
        case_dates = []
        for e in self.html.xpath(self.base_path):
            text = e.text_content()
            date_string = text.replace('Releases for', '').strip()
            if 'No opinions released' in date_string:
                continue
            count = 0
            for a in e.xpath('./following::ul[1]//li//a[not(contains(., "Notice"))][not(contains(., "Rehearing Order"))]'):
                try:
                    case_name_check = self.regex.search(html.tostring(a, method='text', encoding='unicode')).group(2)
                    if case_name_check.strip():
                        count += 1
                except AttributeError:
                    pass
            case_dates.extend([convert_date_string(date_string)] * count)
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '{base}/text()/following::ul[1]//li' \
               '//a[not(contains(., "Notice"))][not(contains(., "Rehearing Order"))]'.format(base=self.base_path)
        docket_numbers = []
        for a in self.html.xpath(path):
            try:
                case_name_check = self.regex.search(html.tostring(a, method='text', encoding='unicode')).group(2)
                if not case_name_check.strip():
                    continue
                else:
                    docket_numbers.append(self.regex.search(html.tostring(a, method='text', encoding='unicode')).group(1))
            except AttributeError:
                pass
        return docket_numbers
