#Scraper for New Hampshire Supreme Court
#CourtID: nh
#Court Short Name: NH
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-06-27

from juriscraper.OpinionSite import OpinionSite

import re
import time
from datetime import date


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.courts.state.nh.us/supreme/opinions/{current_year}/index.htm'.format(
            current_year=date.today().year)
        self.court_id = self.__module__

    def _get_case_names(self):
        path = "id('content')/div//ul//li//a[position()=1]/text()"
        case_names = []
        for text in self.html.xpath(path):
            # Uses a negative look ahead to make sure to get the last occurrence of a docket number.
            match_case_name = re.search('(\d{4}-\d+(?!.*\d{4}-\d+)), (.*)', text)
            case_names.extend([match_case_name.group(2)])
        return case_names

    def _get_download_urls(self):
        path = "id('content')/div//ul//li//a[position()=1]"
        download_url = []
        for element in self.html.xpath(path):
            url = element.xpath('./@href')[0]
            download_url.extend([url])
        return download_url

    def _get_case_dates(self):
        path = "id('content')/div//p[position() > 2]"
        path_2 = './following-sibling::ul[1]//li'
        dates = []
        for p_element in self.html.xpath(path):
            try:
                date_str = str(p_element.xpath('./strong/text()')[0])
                d = date.fromtimestamp(time.mktime(time.strptime(re.sub(' ', '', date_str), '%B%d,%Y')))
                dates.extend([d] * len(p_element.xpath(path_2)))
            except ValueError:
                pass
            except IndexError:
                pass
        return dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "id('content')/div//ul//li//a[position()=1]/text()"
        docket_numbers = []
        for text in self.html.xpath(path):
            match_docket_nr = re.search('(.*\d{4}-\d+), (.*)', text)
            docket_numbers.append(match_docket_nr.group(1))
        return docket_numbers
