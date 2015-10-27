"""Scraper for the D.C. Court of Appeals
CourtID: dc
Court Short Name: D.C.
Author: V. David Zvenyach
Date created:2014-02-21
"""

import time
from datetime import date

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.dccourts.gov/internet/opinionlocator.jsf'

    def _get_download_urls(self):
        return [t for t in self.html.xpath('//table//tr/td[1]/a/@href')]

    def _get_case_names(self):
        return [t for t in self.html.xpath('//table//tr/td[2]/text()')]

    def _get_case_dates(self):
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%b %d, %Y'))) for date_string in self.html.xpath('//table//tr/td[3]/text()')]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        return [t for t in self.html.xpath('//table//tr/td[1]/a/text()')]
