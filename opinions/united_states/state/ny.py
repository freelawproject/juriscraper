# Scraper for New York Court of Appeals
#CourtID: ny
#Court Short Name: NY
#Author: Andrei Chelaru
#Reviewer:
#Date: 2014-07-04

from juriscraper.OpinionSite import OpinionSite

import re
import time
from datetime import date


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        d = date.today()
        self.url = 'http://www.courts.state.ny.us/ctapps/Decisions/{year}/{mon}{yr}/{mon}{yr}.htm'.format(
            year=d.year,
            yr=d.strftime("%y"),
            mon=d.strftime("%b"))
        self.court_id = self.__module__

    def _get_case_names(self):
        path = '''//*[count(td)=4]'''
        case_names = []
        for element in self.html.xpath(path):
            case_name = []
            for d_element in element.xpath('./td[4]/p/font/text()'):
                case_name.append(str(d_element))
            if case_name:
                case_names.append(', '.join(case_name))
        return case_names

    def _get_download_urls(self):
        path = '''//*[count(td)=4]/td[2]//@href[not(contains(., 'DecisionList'))]'''
        return self.html.xpath(path)

    def _get_case_dates(self):
        path = '''//table[@bgcolor="#FFFFFF"]//tr[count(td)=1]//text()[contains(., '2') or contains(., '1')]'''
        dates = self.html.xpath(path)
        case_dates = []
        for index, date_element in enumerate(dates):
            if index < len(dates) - 1:
                path_2 = "//table[@bgcolor='#FFFFFF']//tr[count(td)=1][contains(., '2') or contains(., '1')][{c}]" \
                         "/following-sibling::tr[" \
                         "count(.|//table[@bgcolor='#FFFFFF']//tr[count(td)=1][contains(., '2') or contains(., '1')]" \
                         "[{n}]/preceding-sibling::tr[count(td)=4])" \
                         "=count(//table[@bgcolor='#FFFFFF']//tr[count(td)=1][contains(., '2') or contains(., '1')]" \
                         "[{n}]/preceding-sibling::tr[count(td)=4])]" \
                         "/td[2]//@href[not(contains(., 'DecisionList'))]".format(
                    c=index + 1,
                    n=index + 2
                )
            else:
                path_2 = "//table[@bgcolor='#FFFFFF']//tr[count(td)=1][contains(., '2') or contains(., '1')][{c}]" \
                         "/following-sibling::tr[count(td)=4]/td[2]//@href[not(contains(., 'DecisionList'))]".format(
                    c=index + 1
                )
            d = date.fromtimestamp(time.mktime(time.strptime(re.sub(' ', '', str(date_element)), '%B%d,%Y')))
            case_dates.extend([d] * len(self.html.xpath(path_2)))
        return case_dates

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