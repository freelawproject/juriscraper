#Scraper for New Hampshire Supreme Court
#CourtID: nh
#Court Short Name: NH
#Author: Andrei Chelaru
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
        path = ("id('content')/div//ul//li//a[position()=1]/text()")
        l_case_names = []
        for text in self.html.xpath(path):
            match_case_name = re.sub('\d{4}-\d+,', '', text)
            l_case_names.append(match_case_name)
        return l_case_names

    def _get_download_urls(self):
        path = '''id('content')/div//ul//li//a[position()=1]/@href'''
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = '''id('content')/div//p[position() > 2]'''
        path_2 = './following-sibling::ul[1]//li'
        l_dates = []
        for p_element in self.html.xpath(path):
            try:
                s_date = str(p_element.xpath('./strong/text()')[0])
                obj_date = date.fromtimestamp(
                    time.mktime(time.strptime(re.sub(' ', '', s_date), '%B%d,%Y')))
                nr_opinions = len(p_element.xpath(path_2))
                l_dates.extend([obj_date] * nr_opinions)
            except ValueError:
                pass
            except IndexError:
                pass
        return l_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '''id('content')/div//ul//li//a[position()=1]/text()'''
        l_docket_nr = []
        for text in self.html.xpath(path):
            match_docket_nr = re.search('\d{4}-\d+', text)
            l_docket_nr.append(match_docket_nr.group())
        return l_docket_nr