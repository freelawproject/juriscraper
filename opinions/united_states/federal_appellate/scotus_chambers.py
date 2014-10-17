import time
from datetime import date

from lxml import html

import scotus_slip


class Site(scotus_slip.Site):
    # Note that scotus_relating inherits from this class.
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.supremecourt.gov/opinions/in-chambers.aspx'
        self.court_id = self.__module__

    def _get_case_dates(self):
        path = '//div[@id = "mainbody"]//table/tr/td[1]/text()'
        return [date.fromtimestamp(time.mktime(
            time.strptime(date_string, '%m/%d/%y'))) for date_string in
            self.html.xpath(path)]

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//div[@id = "mainbody"]//table/tr/td[2]'):
            s = html.tostring(e, method='text', encoding='unicode')
            docket_numbers.append(s)

        return docket_numbers

    def _get_precedential_statuses(self):
        return ['In-chambers'] * len(self.case_names)
