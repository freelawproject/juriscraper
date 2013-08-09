# Author: Krist Jin
# Date created: 2013-08-03

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
        self.url = 'http://opinions.aoc.arkansas.gov/WebLink8/browse.aspx?startid=309694'

    def _get_download_urls(self):
        path = '//*[@class="DocumentBrowserNameLink"]/@href'
        return ["http://opinions.aoc.arkansas.gov/WebLink8/"+t for t in self.html.xpath(path)]

    def _get_case_names(self):
        path = '//*[@class="DocumentBrowserNameLink"]/nobr/span[1]/text()'
        return [titlecase(t.upper()) for t in self.html.xpath(path)]

    def _get_case_dates(self):
        path = '//tr/td[@class="DocumentBrowserCell"][5]//nobr/text()'
        result=[]
        for origin_date_string in self.html.xpath(path):
            date_split = origin_date_string.split('/')
            if int(date_split[0]) < 10:
                date_split[0] = "0"+date_split[0]
            if int(date_split[0]) < 10:
                date_split[1] = "0"+date_split[1]
            date_string = date_split[0]+"/"+date_split[1]+"/"+date_split[2]
            result.append(date_string)
            return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y')))]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//tr/td[@class="DocumentBrowserCell"][4]//nobr'):
            s = html.tostring(e, method='text', encoding='unicode')
            docket_numbers.append(titlecase(s))
        return docket_numbers

    def _get_dispositions(self):
        docket_numbers = []
        for e in self.html.xpath('//tr/td[@class="DocumentBrowserCell"][8]//nobr'):
            s = html.tostring(e, method='text', encoding='unicode')
            docket_numbers.append(titlecase(s))
        return docket_numbers


