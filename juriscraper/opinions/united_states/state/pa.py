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
        self.set_regex("(.*)(?:[,-]?\s+Nos?\.)(.*)")
        self.base = "//item[not(contains(title/text(), 'Judgment List'))]" \
                    "[not(contains(title/text(), 'Reargument Table'))]" \
                    "[contains(title/text(), 'No.')]"

    def set_regex(self, pattern):
        self.regex = re.compile(pattern)

    def _get_case_names(self):
        path = "{base}/title/text()".format(base=self.base)
        return map(self._return_case_name, self.html.xpath(path))

    def _return_case_name(self, s):
        match = self.regex.search(s)
        return match.group(1)

    def _get_download_urls(self):
        path = "{base}//@href".format(base=self.base)
        return [item for item in self.html.xpath(path)]

    def _get_case_dates(self):
        path = "{base}/pubdate/text()".format(base=self.base)
        return [convert_date_string(s) for s in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "{base}/title/text()".format(base=self.base)
        return map(self._return_docket_number, self.html.xpath(path))

    def _return_docket_number(self, e):
        return self.regex.search(e).group(2)

    def _get_judges(self):
        path = "{base}/creator/text()".format(base=self.base)
        return list(self.html.xpath(path))
