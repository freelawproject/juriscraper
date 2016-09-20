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
 - 2016-09-19, arderyp: Updated regex.
"""

import re

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.mass.gov/courts/court-info/sjc/about/reporter-of-decisions/opinions.xml'
        self.court_id = self.__module__
        self.court_identifier = 'SJC'
        self.grouping_regex = re.compile("(.*)\s+\((SJC[-\s]+\d+(?:,?;?\s(SJC\s)?\d+)*)\)\s+\((.+)\)")
        self.base_path = "//title[not(contains(., 'List of Un')) and contains(., '{id}')]".format(id=self.court_identifier)
        self.date_group = 4

    def _get_case_names(self):
        names = []
        path = "%s//text()[contains(., '%s')]" % (self.base_path, self.court_identifier)
        for s in self.html.xpath(path):
            name_raw = self.grouping_regex.search(s).group(1)
            names.append(name_raw.replace(';', ' / '))
        return names

    def _get_download_urls(self):
        path = self.base_path + "/following-sibling::link/@href"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        dates = []
        path = self.base_path + "//text()[contains(., '{id}')]".format(id=self.court_identifier)
        for s in self.html.xpath(path):
            date_string = self.grouping_regex.search(s).group(self.date_group)
            dates.append(convert_date_string(date_string))
        return dates

    def _get_docket_numbers(self):
        dockets = []
        path = self.base_path + "//text()[contains(., '{id}')]".format(id=self.court_identifier)
        for s in self.html.xpath(path):
            docket_raw = self.grouping_regex.search(s).group(2)
            docket_clean = docket_raw.replace('SJC', '').replace(';', '').replace(',', '')
            docket = ', '.join(docket_clean.split())
            dockets.append(docket)
        return dockets

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)
