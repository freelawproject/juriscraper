# Scraper for Supreme Court of Oklahoma
# CourtID: okla
# Court Short Name: OK
# Court Contact: webmaster@oscn.net
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05

from datetime import date
import time
import re

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        d = date.today()
        self.elements = []
        self.len_elements = 0
        self.general_path = "//a[contains(./text(), '{year}')]".format(year=d.year)
        self.url = 'http://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKCSSC&year={year}&level=1'.format(
            year=d.year
        )

    def _get_download_urls(self):
        path = "{gen_path}/@href".format(gen_path=self.general_path)
        return list(self.html.xpath(path))

    def _get_case_names(self):
        # Depends on _get_case_dates being run prior.
        return list(map(self._return_desired_group, self.elements, [3] * self.len_elements))

    def _get_case_dates(self):
        path = "{gen_path}/text()".format(gen_path=self.general_path)
        self.elements = self.html.xpath(path)
        self.len_elements = len(self.elements)
        return list(map(self._return_desired_group, self.elements, [2] * self.len_elements))

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_neutral_citations(self):
        return list(map(self._return_desired_group, self.elements, [1] * self.len_elements))

    @staticmethod
    def _return_desired_group(element_text, nr):
        desired_str = re.search(r'([^,]+), (\d{2}.\d{2}.\d{4}), (.*)', element_text).group(nr)
        if nr == 2:
            return date.fromtimestamp(time.mktime(time.strptime(desired_str, '%m/%d/%Y')))
        else:
            return desired_str
