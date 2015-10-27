# Scraper for New York Appellate Divisions 1st Dept.
#CourtID: nyappdiv_1st
#Court Short Name: NY
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-04

import time
from datetime import date
from dateutil.rrule import rrule, MONTHLY

import re
from juriscraper.OpinionSite import OpinionSite
from juriscraper.AbstractSite import logger


class Site(OpinionSite):

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)

        self.back_scrape_iterable = [i.date() for i in rrule(
            MONTHLY,
            dtstart=date(2003, 11, 1),
            until=date(2015, 8, 30),
        )]

        # This is the URL for the current month
        self.url = 'http://www.courts.state.ny.us/reporter/slipidx/aidxtable_1.shtml'
        self.court_id = self.__module__

    def _get_case_names(self):
        path = '//tr[td[4]]//a[contains(./@href, "3d")]/text()'
        return self.html.xpath(path)

    def _get_download_urls(self):
        path = '//tr[td[4]]//a/@href[contains(., "3d")]'
        return self.html.xpath(path)

    def _get_case_dates(self):
        path = '//caption//text()'
        dates = self.html.xpath(path)
        case_dates = []
        for index, case_date in enumerate(dates):
            path_2 = "count((//table[./caption])[{c}]/tr[.//@href])".format(c=index + 1)
            d = date.fromtimestamp(time.mktime(time.strptime(re.sub('Cases Decided ', '', case_date), '%B %d, %Y')))
            case_dates.extend([d] * int(self.html.xpath(path_2)))
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//tr[contains(./td[1]/a/@href, "3d")]/td[3]'
        return map(self._add_str_to_list_where_empty_element, self.html.xpath(path))

    def _get_judges(self):
        path = '//tr[contains(./td[1]/a/@href, "3d")]/td[2]'
        return map(self._add_str_to_list_where_empty_element, self.html.xpath(path))

    @staticmethod
    def _add_str_to_list_where_empty_element(element):
        string_list = element.xpath('./text()')
        if string_list:
            return string_list[0]
        else:
            return ''

    def _download_backwards(self, d):
        self.crawl_date = d
        logger.info("Running backscraper with date: %s" % d)
        self.url = 'http://www.courts.state.ny.us/reporter/slipidx/aidxtable_1_{year}_{month}.shtml'.format(
            year=d.year,
            month=d.strftime("%B")
        )
