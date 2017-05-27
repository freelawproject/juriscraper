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
    """If you discover new examples that failed the
    regex below, please add them to the test_mass
    method in test_everything.py
    """
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.mass.gov/courts/court-info/sjc/about/reporter-of-decisions/opinions.xml'
        self.court_id = self.__module__
        self.court_identifier = 'SJC'
        # If you discover new examples that failed the
        # regex below, please add them to the test_mass
        # method in test_everything.py
        self.regex = "(.*)\s+\((%s[-\s]+\d+(?:,?;?\s(%s\s)?\d+)*)\)" % (self.court_identifier, self.court_identifier)
        self.date_group = 4
        self.set_local_variables()

    def set_local_variables(self):
        self.grouping_regex = re.compile(self.regex)
        pattern_base_path = "//title[not(contains(., 'List of Un')) and contains(., '%s ') or contains(., '%s-')]"
        pattern_court_path = "%s//text()[contains(., '(%s ') or contains(., '(%s-')]"
        self.base_path = pattern_base_path % (self.court_identifier, self.court_identifier)
        self.court_path = pattern_court_path % (self.base_path, self.court_identifier, self.court_identifier)
        self.date_path = "%s/../../published/text()" % self.court_path

    def _get_case_names(self):
        names = []
        for s in self.html.xpath(self.court_path):
            name_raw = self.grouping_regex.search(s).group(1)
            names.append(name_raw.replace(';', ' / '))
        return names

    def _get_download_urls(self):
        path = self.base_path + "/following-sibling::link/@href"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        """We were previously extracting dates from the link title text
        but massappct examples started popping up that did not include
        a date in the title text. We are not sure why the court is even
        including the date in the title text when their XML also includes
        a <published> tag. For now we are relying on the date in the
        <published> tag, as parsing this is easier than using complex
        regular expressions and relying on the court to repond if/when
        dates are missing in the titles.
        """
        return [convert_date_string(s.strip()) for s in self.html.xpath(self.date_path)]

    def _get_docket_numbers(self):
        dockets = []
        for s in self.html.xpath(self.court_path):
            docket_raw = self.grouping_regex.search(s).group(2)
            docket = docket_raw.replace(';', ',').replace(self.court_identifier + ',', self.court_identifier)
            dockets.append(docket)
        return dockets

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)
