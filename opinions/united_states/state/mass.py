"""
Scraper for Massachusetts Supreme Court
CourtID: mass
Court Short Name: MS
Author: Andrei Chelaru
Reviewer: mlr
History:
 - 2014-07-12: Created.
 - 2014-08-05, mlr: Updated regex.
 - 2014-09-18, mlr: Updated regex.
"""

import re
import time
from datetime import date
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.mass.gov/courts/court-info/sjc/about/reporter-of-decisions/opinions.xml'
        self.court_id = self.__module__
        self.court_identifier = 'SJC'
        self.grouping_regex = re.compile("(.*)\s+\((SJC[-\s]+\d+(?:, \d+)*)\)\s+\((.+)\)")
        self.base_path = "//title[not(contains(., 'List of Un')) and contains(., '{id}')]".format(id=self.court_identifier)

    def _get_case_names(self):
        path = self.base_path + "//text()[contains(., '{id}')]".format(
            id=self.court_identifier
        )
        return [self.grouping_regex.search(s).group(1) for s in self.html.xpath(path)]

    def _get_download_urls(self):
        path = self.base_path + "/following-sibling::link/@href"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        dates = []
        path = self.base_path + "//text()[contains(., '{id}')]".format(id=self.court_identifier)
        for s in self.html.xpath(path):
            s = self.grouping_regex.search(s).group(3)
            dates.append(date.fromtimestamp(time.mktime(time.strptime(s, '%B %d, %Y'))))
        return dates

    def _get_docket_numbers(self):
        path = self.base_path + "//text()[contains(., '{id}')]".format(id=self.court_identifier)
        return [self.grouping_regex.search(s).group(2)
                for s in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)
