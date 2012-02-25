import scotus_slip
import time
from datetime import date

class Site(scotus_slip.Site):
    # Note that scotus_relating inherits from this class.
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.supremecourt.gov/opinions/in-chambers.aspx'
        self.court_id = self.__module__

    def _get_case_dates(self):
        path = '//div[@id = "maincolumn"]//table/tr/td[1]/text()'
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%y')))
                    for date_string in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = '//div[@id = "maincolumn"]//table/tr/td[2]/text()'
        return [docket_number for docket_number in self.html.xpath(path)]
