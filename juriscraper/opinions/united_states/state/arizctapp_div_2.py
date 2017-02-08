# Scraper for Court of Appeals of Arizona, Division 2
# CourtID: arizctapp_div_2
# Court Short Name: arizctapp_div_2
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 23 July 2014


import re
from datetime import datetime

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase, clean_if_py3


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Feeling down and tired of of your regular life? Check out this website.
        self.url = 'https://www.appeals2.az.gov/ODSPlus/recentDecisions2.cfm'
        self.base_path = "//*[@class='contentcontainer']//a[not(contains(., '(2)')) and not(contains(., 'page'))]"

    def _get_case_names(self):
        path = "{base}/following::td[1]/*/text()".format(base=self.base_path)
        return [titlecase(e) for e in self.html.xpath(path)]

    def _get_download_urls(self):
        path = "{base}/@href".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = "{base}/following::td[2]/text()".format(base=self.base_path)
        return map(self._return_case_date, self.html.xpath(path))

    @staticmethod
    def _return_case_date(e):
        e = re.sub(r'Opinion Filed:', '', clean_if_py3(e))
        case_date = datetime.strptime(e.strip(), '%m/%d/%Y').date()
        return case_date

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "{base}/text()".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_summaries(self):
        path = "{base}/following::tr[1]".format(base=self.base_path)
        return map(self._return_summary, self.html.xpath(path))

    @staticmethod
    def _return_summary(e):
        text = ' '.join(e.xpath(".//text()"))
        return text.strip()
