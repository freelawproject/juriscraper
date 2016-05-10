"""
Author: Michael Lissner
Date created: 2013-04-05
Revised by Taliah Mirmalek on 2014-02-07
Scraper for the Supreme Court of Arizona
CourtID: ariz
Court Short Name: Ariz.
"""

import time
from datetime import date

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.azcourts.gov/opinions/SearchOpinionsMemoDecs.aspx?court=999'

    def _get_download_urls(self):
        path = '//a[contains(@id , "hypCaseNum")]/@href'
        return [t for t in self.html.xpath(path)]

    def _get_case_names(self):
        path = '//span[contains(@id , "lblTitle")]//text()'
        return [titlecase(t.upper()) for t in self.html.xpath(path)]

    def _get_case_dates(self):
        path = '//span[contains(@id , "FilingDate")]//text()'
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y')))
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        statuses = []
        path = '//*[contains(@id, "DecType")]/text()'
        for s in self.html.xpath(path):
            if 'OPINION' in s:
                statuses.append('Published')
            elif 'MEMORANDUM' in s:
                statuses.append('Unpublished')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_docket_numbers(self):
        path = '//a[contains(@id , "hypCaseNum")]//text()'
        return [t for t in self.html.xpath(path)]
