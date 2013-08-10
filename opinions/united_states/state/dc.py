# Author: Krist Jin
# Reviewer: Michael Lissner
# Date created:2013-08-03

import time
from datetime import date
from datetime import datetime

from juriscraper.GenericSite import GenericSite


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.cadc.uscourts.gov/internet/opinions.nsf/OpinionsByMonday'

    def _get_download_urls(self):
        path = '//opinion/div/span/a/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//opinion/div/span[@class="column-two"]//text()'
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = '//opinion/div/span[@class="column-two myDemphasize"]//text()'
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y')))
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//opinion/div/span/a//text()'
        return list(self.html.xpath(path))

