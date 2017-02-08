#  Scraper for Pennsylvania Supreme Court
# CourtID: pa
# Court Short Name: pa
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 21 July 2014

import re

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.regex = False
        self.url = 'http://www.pacourts.us/assets/rss/SupremeOpinionsRss.ashx'
        self.set_regex(r"(.*)(?:[,-]?\s+Nos?\.)(.*)")
        self.base = "//item[not(contains(title/text(), 'Judgment List'))]" \
                    "[not(contains(title/text(), 'Reargument Table'))]" \
                    "[contains(title/text(), 'No.')]"

    def set_regex(self, pattern):
        self.regex = re.compile(pattern)

    def _get_case_names(self):
        path = "{base}/title/text()".format(base=self.base)
        return list(map(self.return_case_name, self.html.xpath(path)))

    def _get_download_urls(self):
        return [href for href in self.html.xpath('%s//@href' % self.base)]

    def _get_case_dates(self):
        path = "{base}/pubdate/text()".format(base=self.base)
        return [convert_date_string(s) for s in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        return self.return_path_text('%s/title' % self.base)

    def _get_judges(self):
        return self.return_path_text('%s/creator' % self.base)

    def return_case_name(self, s):
        match = self.regex.search(s.replace(r'\n', '\n'))
        return match.group(1)

    def return_docket_number(self, e):
        return self.regex.search(e.replace(r'\n', '\n')).group(2)

    def return_path_text(self, path):
        return [element.text_content() for element in self.html.xpath(path)]
