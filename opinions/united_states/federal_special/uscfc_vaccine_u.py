"""Scraper for the United States Court of Federal Claims
CourtID: uscfc
Court Short Name: Fed. Cl."""

import uscfc
import time
import datetime
from datetime import date
import re
from lxml import html

class Site(uscfc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = (
            'http://www.uscfc.uscourts.gov/opinions_decisions_vaccine/Unpublished')
        self.court_id = self.__module__

    # Exclude rows without opinions by ensuring there is a sibling row that
    # contains an anchor. We must do this in each of the below.
    def _get_case_dates(self):
        dates = []
        for txt in self.html.xpath(
            '//div[2]/table/tbody/tr/td[../td[4]/a]/span/text()'):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(
                txt.strip(), '%m/%d/%Y'))))
        return dates

    def _get_judges(self):
        judges = []
        for txt in self.html.xpath(
            '//div[2]/table/tbody/tr/td[2][../td[4]/a]/text()'):
            judges.append(txt)
        return judges

    def _get_case_names(self):
        case_names = []
        for txt in self.html.xpath(
                '//div[2]/table/tbody/tr/td[3][../td[4]/a]/a/text()'):        
            case_names.append(txt.strip()[:-8].replace('[', '').strip())
        return case_names

    def _get_docket_numbers(self):
        docket_numbers = []
        regex = re.compile("\d\d.\d*[a-zA-Z]")        
        return [regex.search(html.tostring(
                            ele, method ='text', encoding='unicode')).group(0)
            for ele in self.html.xpath(
                '//div[2]/table/tbody/tr/td[3][../td[4]/a]')]
        return docket_numbers

    def _get_precedential_statuses(self):
        return ['Unpublished'] * len(self.case_names)