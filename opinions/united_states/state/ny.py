# Scraper for New York Court of Appeals
#CourtID: ny
#Court Short Name: NY
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-04

from juriscraper.OpinionSite import OpinionSite

import re
from datetime import date


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.crawl_date = date.today()
        # http://www.courts.state.ny.us/ctapps/Decisions/2014/Jul14/Jul14.htm
        self.url = 'http://www.courts.state.ny.us/ctapps/Decisions/{year}/{mon}{yr}/{mon}{yr}.htm'.format(
            year=self.crawl_date.year,
            yr=self.crawl_date.strftime("%y"),
            mon=self.crawl_date.strftime("%b"))
        self.court_id = self.__module__

    def _get_case_names(self):
        path = '''//*[count(td)=4]'''  # Any element with four td's
        case_names = []
        for element in self.html.xpath(path):
            case_name_parts = []
            for t in element.xpath('./td[4]/p/font/text()'):
                case_name_parts.append(t)
            if case_name_parts:
                case_names.append(', '.join(case_name_parts))
        return case_names

    def _get_download_urls(self):
        path = '''//*[count(td)=4]/td[2]//@href[not(contains(., 'DecisionList'))]'''
        return self.html.xpath(path)

    def _get_case_dates(self):
        path = '''//*[count(td)=4]/td[2]//@href[not(contains(., 'DecisionList'))]'''
        return [self.crawl_date] * len(self.html.xpath(path))

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '''//*[count(td)=4]'''
        docket_numbers = []
        for element in self.html.xpath(path):
            docket_nr = []
            for d_element in element.xpath('./td[1]/div/p/strong/font/text()'):
                docket_nr.append(re.sub('[\t\n\r\f\v]', '', str(d_element)))
            if docket_nr:
                docket_numbers.append(', '.join(docket_nr))
        return docket_numbers
