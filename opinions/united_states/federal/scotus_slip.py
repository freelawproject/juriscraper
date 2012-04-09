from juriscraper.GenericSite import GenericSite
import time
from datetime import date
from lib.string_utils import titlecase

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.supremecourt.gov/opinions/slipopinions.aspx'
        self.court_id = self.__module__

    def _get_case_names(self):
        return [titlecase(text) for text in self.html.xpath('//div[@id = "maincolumn"]//table/tr/td/a/text()')]

    def _get_download_urls(self):
        return [e for e in self.html.xpath('//div[@id = "maincolumn"]//table/tr/td/a/@href')]

    def _get_case_dates(self):
        path = '//div[@id = "maincolumn"]//table/tr/td[2]/text()'
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%y')))
                    for date_string in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = '//div[@id = "maincolumn"]//table/tr/td[3]/text()'
        return [docket_number for docket_number in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        statuses = []
        for _ in range(0, len(self.case_names)):
            if 'slipopinion' in self.url:
                statuses.append("Published")
            elif 'in-chambers' in self.url:
                statuses.append("In-chambers")
            elif 'relatingtoorders' in self.url:
                statuses.append("Relating-to")
        return statuses
