# Scraper for Supreme Court of Oklahoma
# CourtID: okla
# Court Short Name: OK
# Court Contact: webmaster@oscn.net
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05

import re
from datetime import date

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.elements = []
        self.base_path = False
        self.year = date.today().year
        self.regex = r"([^,]+), (\d{2}.\d{2}.\d{4}), (.*)"
        self.url = (
            "http://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKCSSC&year=%d&level=1"
            % self.year
        )

    def set_base_path(self):
        # All test files should be edited to use year value of 2018
        year = 2018 if self.test_mode_enabled() else self.year
        self.base_path = "//a[contains(./text(), '%d')]" % year

    def _download(self, request_dict={}):
        self.set_base_path()
        html = super()._download(request_dict)
        self.elements = html.xpath(self.base_path)
        return html

    def _get_download_urls(self):
        path = f"{self.base_path}/@href"
        return self.html.xpath(path)

    def _get_case_dates(self):
        return [self._return_substring(e, 2) for e in self.elements]

    def _get_case_names(self):
        return [self._return_substring(e, 3) for e in self.elements]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_citations(self):
        return [self._return_substring(e, 1) for e in self.elements]

    def _return_substring(self, element, group):
        text = element.text_content()
        substring = re.search(self.regex, text).group(group)
        return substring if group != 2 else convert_date_string(substring)
