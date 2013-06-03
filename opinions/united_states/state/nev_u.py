# Author: Michael Lissner
# Date created: 2013-06-03

from juriscraper.lib.string_utils import titlecase
from juriscraper.GenericSite import GenericSite

from datetime import date
import time


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.nevadajudiciary.us/index.php/unpublished-orders'

    def _get_download_urls(self):
        path = '//div[@id = "content"]/div/table/tr/td[3]/a/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//div[@id = "content"]/div/table/tr/td[2]/text()'
        return [titlecase(case) for case in self.html.xpath(path)]

    def _get_case_dates(self):
        path = '//div[@id = "content"]/div/table/tr/td[3]//text()'
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%B %d, %Y')))
                for date_string in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = '//div[@id = "content"]/div/table/tr/td[1]//text()'
        return list(self.html.xpath(path))

    def _get_precedential_statuses(self):
        return ['Unpublished'] * len(self.case_names)

