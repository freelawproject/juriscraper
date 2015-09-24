import time
from datetime import date

from lxml import html

import scotus_slip


class Site(scotus_slip.Site):
    # Note that scotus_relating inherits from this class.
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.supremecourt.gov/opinions/in-chambers.aspx'
        self.back_scrape_url = 'http://www.supremecourt.gov/opinions/in-chambers/{}'
        self.back_scrape_iterable = range(5, 16)
        self.court_id = self.__module__

    def _get_case_dates(self):
        path = '//div[@id = "mainbody"]//table//tr/td[1]/text()'
        case_dates = []
        for date_string in self.html.xpath(path):
            try:
                case_date = date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%y')))
            except ValueError:
                case_date = date.fromtimestamp(time.mktime(time.strptime(date_string, '%m-%d-%y')))
            case_dates.append(case_date)
        return case_dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//div[@id = "mainbody"]//table//tr/td[2]'):
            s = html.tostring(e, method='text', encoding='unicode')
            docket_numbers.append(s)

        return docket_numbers

    def _get_precedential_statuses(self):
        return ['In-chambers'] * len(self.case_names)
