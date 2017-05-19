# Scraper for Florida Supreme Court
# CourtID: fla
# Court Short Name: fla
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 21 July 2014

import re
from lxml import html
from datetime import datetime

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.regex = re.compile("(S?C\d+-\d+)(.*)")
        self.regex_date = re.compile(r'(?:.*\s)?(\w+\s\d+,\s\d{4})(?:.*)?')
        self.url = 'http://www.floridasupremecourt.org/decisions/opinions.shtml'

    def _download(self, request_dict={}):
        html = super(Site, self)._download(request_dict)
        self.base_path = "//h2[contains(., '%s')]" % self.extract_year_from_h1(html)
        return html

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
            if 'No opinions released' in text:
                continue
            date_string = self.regex_date.search(text).group(1)
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

    def extract_year_from_h1(self, html):
        """For testability with example files from previous years,
        we can't use the current year in the base_path search, and
        instead need to extract the year from the pages <h1> tag.
        This is also handy early in the calendar year if/when the
        court is publishing new opinions for the end of the previous
        year
        """
        year_string = html.xpath('//h1')[0].text_content().split()[3]
        # Basic validation of year
        if len(year_string) != 4 or not year_string.startswith('20'):
            raise InsanityException('Extracted year "%s") appears to be invalid' % year_string)
        # If running live scrape, year should always be this year or last year
        if self.method != 'LOCAL':
            this_year = datetime.today().year
            if int(year_string) not in [this_year, this_year - 1]:
                raise InsanityException('Year ("%s") too far in the future or past' % year_string)
        return year_string
