# Author: Michael Lissner
# Date created: 2013-06-03

import time
from datetime import date

from juriscraper.GenericSite import GenericSite


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.nevadajudiciary.us/index.php/advance-opinions'

    def _get_download_urls(self):
        path = '//div[@id = "content"]/div/table/tr/td[4]/a/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//div[@id = "content"]/div/table/tr/td[3]/text()'
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = '//div[@id = "content"]/div/table/tr/td[4]//text()'
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%B %d, %Y')))
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//div[@id = "content"]/div/table/tr/td[2]//text()'
        return list(self.html.xpath(path))
