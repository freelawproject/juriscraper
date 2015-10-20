# Scraper for New York Court of Appeals
#CourtID: ny
#Court Short Name: NY
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-04

import re
from datetime import date

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
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
                if t.strip():
                    case_name_parts.append(t)
            if not case_name_parts:
                # No hits for first XPath, try another that sometimes works.
                for t in element.xpath('./td[4]/text()'):
                    if t.strip():
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
        path = '''//*[count(td)=4]/td[1]'''
        docket_numbers = []
        for elem in self.html.xpath(path):
            text_nodes = elem.xpath('.//text()')
            t = ', '.join(text_nodes)
            if re.search(r'\d', t):
                docket_numbers.append(t)
        return docket_numbers
