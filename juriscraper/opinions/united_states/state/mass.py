"""
Scraper for Massachusetts Supreme Court
CourtID: mass
Court Short Name: MS
Author: Andrei Chelaru
Court Contact: SJCReporter@sjc.state.ma.us (617) 557-1030
Reviewer: mlr
History:
 - 2014-07-12: Created.
 - 2014-08-05, mlr: Updated regex.
 - 2014-09-18, mlr: Updated regex.
 - 2016-09-19, arderyp: Updated regex.
 - 2017-11-29, arderyp: Moved from RSS source to HTML
    parsing due to website redesign
"""

import datetime
import re

from juriscraper.lib.string_utils import clean_string, convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    """If you discover new examples that failed the
    regex below, please add them to the test_mass
    method in test_everything.py
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.mass.gov/service-details/new-opinions"
        self.court_id = self.__module__
        self.court_identifier = "SJC"
        # If you discover new examples that failed the
        # regex below, please add them to the test_mass
        # method in test_everything.py
        self.regex = r"(.*)\s+\((.*)\)\s+\((.*)\)"
        self.year = datetime.datetime.now().year

    def _download(self, request_dict={}):
        """For tests, we must extract the year from the
        HTML instead of using the current year, otherwise
        test comparisons for example files created in
        past years will fail
        """
        html = super()._download(request_dict)
        if self.test_mode_enabled():
            path = '//h2[contains(./text(), "Today\'s Published Opinions")]'
            header_text = html.xpath(path)[0].text_content()
            self.year = int(header_text.split(" ")[-1])
        self.set_local_variables()
        return html

    def set_local_variables(self):
        """The base xpath below requires '<current year>)' in
        the link text via the include_date definition. This
        means we might miss some opinions, when the court
        publishes line items without this pattern, but the
        only alternative it to email Mass every time there
        is an issue. Line items missing this pattern is not
        normal, but doesn't look altogether uncommon.
        Consequently, this approach is less than ideal, but
        it works for the time being.
        """
        exclude_list = "not(contains(., 'List of Un'))"
        include_date = "contains(., '%d)')" % self.year
        include_court = "contains(., '{} ') or contains(., '{}-')".format(
            self.court_identifier,
            self.court_identifier,
        )
        self.base_path = "//a/text()[{}][{}][{}]".format(
            exclude_list,
            include_date,
            include_court,
        )
        self.grouping_regex = re.compile(self.regex)

    def _get_case_names(self):
        names = []
        for s in self.html.xpath(self.base_path):
            s = clean_string(s)
            name_raw = self.grouping_regex.search(s).group(1)
            name = name_raw.replace(";", " / ")
            names.append(name)
        return names

    def _get_download_urls(self):
        path = f"{self.base_path}/parent::a/@href"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        dates = []
        for s in self.html.xpath(self.base_path):
            s = clean_string(s)
            date_string = self.grouping_regex.search(s).group(3)
            dates.append(convert_date_string(date_string))
        return dates

    def _get_docket_numbers(self):
        dockets = []
        for s in self.html.xpath(self.base_path):
            s = clean_string(s)
            docket_raw = self.grouping_regex.search(s).group(2)
            docket = docket_raw.replace(";", ",").replace(
                f"{self.court_identifier},", self.court_identifier
            )
            dockets.append(docket)
        return dockets

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)
