# Scraper for Massachusetts Supreme Court
# CourtID: mass
#Court Short Name: MS
#Author: Andrei Chelaru
#Reviewer:
#Date: 2014-07-12

from juriscraper.OpinionSite import OpinionSite
import re
import time
from datetime import date
from lxml import html, etree


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.mass.gov/courts/court-info/sjc/about/reporter-of-decisions/opinions.xml'
        self.court_id = self.__module__
        self.court_identifier = 'SJC'
        self.grouping_regex = re.compile("(.*) \((SJC \d+)\) \((.+)\)")

    def _get_case_names(self):
        return [self.grouping_regex.search(s).group(1)
                for s in self.html.xpath("//title[not(contains(., 'List of Un')) "
                                         "and contains(., '{id}')]"
                                         "//text()[contains(., '{id}')]".format(id=self.court_identifier))]

    def _get_download_urls(self):
        return list(self.html.xpath("//title[not(contains(., 'List of Un'))"
                                    " and contains(., '{id}')]"
                                    "/following-sibling::link/@href".format(id=self.court_identifier)))

    def _get_case_dates(self):
        print(etree.tostring(self.html))
        dates = []
        for s in self.html.xpath("//title[not(contains(., 'List of Un')) "
                                         "and contains(., '{id}')]"
                                         "//text()[contains(., '{id}')]".format(id=self.court_identifier)):
            s = self.grouping_regex.search(s).group(3)
            dates.append(date.fromtimestamp(time.mktime(time.strptime(s, '%B %d, %Y'))))
        return dates

    def _get_docket_numbers(self):
        return [self.grouping_regex.search(s).group(2)
                for s in self.html.xpath("//title[not(contains(., 'List of Un')) "
                                         "and contains(., '{id}')]"
                                         "//text()[contains(., '{id}')]".format(id=self.court_identifier))]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)