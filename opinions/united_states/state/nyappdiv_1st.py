# Scraper for New York Appellate Divisions 1st Dept.
#CourtID: nyappdiv_1st
#Court Short Name: NY
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-04

from juriscraper.opinions.united_states.state import ny

import re
import time
from datetime import date


class Site(ny.Site):
    def __init__(self):
        super(Site, self).__init__()
        # This is the URL for the past months
        # d = date.today()
        # self.url = 'http://www.courts.state.ny.us/reporter/slipidx/aidxtable_1_{year}_{month}.shtml'.format(
        #     year=d.year,
        #     mon=d.strftime("%B"))

        # This is the URL for the current month
        self.url = 'http://www.courts.state.ny.us/reporter/slipidx/aidxtable_1.shtml'
        self.court_id = self.__module__

    def _get_case_names(self):
        path = '''//tr//a[contains(./@href, '3d')]/text()'''
        return self.html.xpath(path)

    def _get_download_urls(self):
        path = '''//tr//a/@href[contains(., '3d')]'''
        return self.html.xpath(path)

    def _get_case_dates(self):
        path = '''//caption//text()'''
        dates = self.html.xpath(path)
        case_dates = []
        for index, case_date in enumerate(dates):
            path_2 = "count(//table[./caption][{c}]//tr[.//@href])".format(c=index + 1)
            d = date.fromtimestamp(time.mktime(time.strptime(re.sub('Cases Decided ', '', case_date), '%B %d, %Y')))
            case_dates.extend([d] * int(self.html.xpath(path_2)))
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '''//tr[contains(./td[1]/a/@href, '3d')]/td[3]'''
        return map(self._add_str_to_list_where_empty_element, self.html.xpath(path))

    def _get_judges(self):
        path = '''//tr[contains(./td[1]/a/@href, '3d')]/td[2]'''
        return map(self._add_str_to_list_where_empty_element, self.html.xpath(path))

    @staticmethod
    def _add_str_to_list_where_empty_element(element):
        string_list = element.xpath('./text()')
        if string_list:
            return string_list[0]
        else:
            return ''
