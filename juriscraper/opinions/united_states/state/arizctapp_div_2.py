# Scraper for Court of Appeals of Arizona, Division 2
# CourtID: arizctapp_div_2
# Court Short Name: arizctapp_div_2
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 23 July 2014


import re
from datetime import datetime

from juriscraper.lib.string_utils import clean_if_py3, titlecase
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Feeling down and tired of of your regular life? Check out this website.
        self.url = "https://www.appeals2.az.gov/ODSPlus/recentDecisions2.cfm"
        self.base_path = "//*[@class='contentcontainer']//a[not(contains(., '(2)')) and not(contains(., 'page'))]"

    def _get_case_names(self):
        path = f"{self.base_path}/following::td[1]/*/text()"
        return [titlecase(e) for e in self.html.xpath(path)]

    def _get_download_urls(self):
        path = f"{self.base_path}/@href"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = f"{self.base_path}/following::td[2]/text()"
        return list(map(self._return_case_date, self.html.xpath(path)))

    @staticmethod
    def _return_case_date(e):
        e = re.sub(r"Opinion Filed:", "", clean_if_py3(e))
        case_date = datetime.strptime(e.strip(), "%m/%d/%Y").date()
        return case_date

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        path = f"{self.base_path}/text()"
        return list(self.html.xpath(path))

    def _get_summaries(self):
        path = f"{self.base_path}/following::tr[1]"
        return list(map(self._return_summary, self.html.xpath(path)))

    @staticmethod
    def _return_summary(e):
        text = " ".join(e.xpath(".//text()"))
        return text.strip()
