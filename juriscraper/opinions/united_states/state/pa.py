# -*- coding: utf-8 -*-

# Scraper for Pennsylvania Supreme Court
# CourtID: pa
# Court Short Name: pa
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 21 July 2014

import re

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.lib.string_utils import clean_string


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
        path = "%s/title" % self.base
        return [self.return_case_name(s) for s in self.return_path_text(path)]

    def _get_download_urls(self):
        path = '%s//@href' % self.base
        return [href for href in self.html.xpath(path)]

    def _get_case_dates(self):
        path = "%s/pubdate" % self.base
        return [convert_date_string(s) for s in self.return_path_text(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "%s/title" % self.base
        return [self.return_docket_number(s) for s in self.return_path_text(path)]

    def _get_judges(self):
        return self.return_path_text('%s/creator' % self.base)

    def return_path_text(self, path):
        return [self.sanitize_text(element.text_content()) for element in self.html.xpath(path)]

    def return_case_name(self, text):
        text = clean_string(text)
        return self.regex.search(text).group(1)

    def return_docket_number(self, text):
        text = clean_string(text)
        return self.regex.search(text).group(2)

    def sanitize_text(self, text):
        text = clean_string(text)
        return text.replace(r'\n', '\n').replace(u'–', '-')
