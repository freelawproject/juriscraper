# Scraper for Florida Supreme Court
# CourtID: fla
# Court Short Name: fla
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 21 July 2014

import re
from datetime import datetime

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.floridasupremecourt.org/decisions/opinions.shtml'
        self.regex = re.compile("(S?C\d+-\d+)(.*)")
        self.regex_date = re.compile(r'(?:.*\s)?(\w+\s\d+,\s\d{4})(?:.*)?')
        self.path_anchor_qualifier = 'not(contains(., "Notice"))][not(contains(., "Rehearing Order"))'
        self.cases = []

    def _download(self, request_dict={}):
        html = super(Site, self)._download(request_dict)
        self._extract_cases_from_html(html)
        return html

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

    def _extract_cases_from_html(self, html):
        year = self.extract_year_from_h1(html)
        path_dates = "//h2[contains(., '%s')]" % year
        for h2 in html.xpath(path_dates):
            text_date = h2.text_content().strip()
            if not text_date or 'No opinions released' in text_date:
                continue
            date_string = self.regex_date.search(text_date).group(1)
            date = convert_date_string(date_string)
            next_tag = h2.getnext().tag
            if not self.cases and next_tag == 'p':
                # Sometimes court puts most recent date's opinions in
                # its own box at the top of the page, in a format that
                # doesn't conform with the other date sections below
                path = './/a[%s]' % self.path_anchor_qualifier
                anchors = h2.getparent().xpath(path)
            else:
                path = './following::ul[1]//a[%s]' % self.path_anchor_qualifier
                anchors = h2.xpath(path)
            for anchor in anchors:
                text_anchor = anchor.text_content()
                match = self.regex.search(text_anchor)
                if not match:
                    continue
                self.cases.append({
                    'date': date,
                    'docket': match.group(1),
                    'name': match.group(2).strip(),
                    'url': anchor.xpath('./@href')[0],
                })

    def _get_case_names(self):
        return [case['name'] for case in self.cases]

    def _get_download_urls(self):
        return [case['url'] for case in self.cases]

    def _get_case_dates(self):
        return [case['date'] for case in self.cases]

    def _get_docket_numbers(self):
        return [case['docket'] for case in self.cases]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)
