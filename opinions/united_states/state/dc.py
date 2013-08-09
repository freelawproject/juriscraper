# Author: Krist Jin
# Date created:2013-08-03

import time
from datetime import date
from datetime import datetime
from lxml import html

from juriscraper.GenericSite import GenericSite
from juriscraper.lib.string_utils import titlecase


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.cadc.uscourts.gov/internet/opinions.nsf/OpinionsByMonday'

    def _get_download_urls(self):
        path = '/html/body/div[2]/div/div[2]/div[2]/div[2]/div/opinion/div/span/a/@href'
        return [t for t in self.html.xpath(path)]

    def _get_case_names(self):
        path = '/html/body/div[2]/div/div[2]/div[2]/div[2]/div/opinion/div/span[@class="column-two"]//text()'
        return [titlecase(t.upper()) for t in self.html.xpath(path)]

    def _get_case_dates(self):
        path = '/html/body/div[2]/div/div[2]/div[2]/div[2]/div/opinion/div/span[@class="column-two myDemphasize"]//text()'
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y')))
                    for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '/html/body/div[2]/div/div[2]/div[2]/div[2]/div/opinion/div/span/a//text()'
        return [t for t in self.html.xpath(path)]

