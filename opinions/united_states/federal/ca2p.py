from GenericSite import GenericSite
import time
from datetime import date
from lxml import html

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.ca2.uscourts.gov/decisions?IW_DATABASE=OPN&IW_FIELD_TEXT=*&IW_SORT=-Date&IW_BATCHSIZE=100'
        self.court_id = self.__module__

    def _get_case_names(self):
        return [e for e in self.html.xpath('//table/td[2]/text()')]

    def _get_download_links(self):
        return [e for e in self.html.xpath('//table/td/b/a/@href')]

    def _get_case_dates(self):
        dates = []
        for e in self.html.xpath('//table/td[3]/text()'):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(e, '%m-%d-%Y'))))
        return dates

    def _get_docket_numbers(self):
        return [html.tostring(e, method='text') for e in self.html.xpath('//table/td/b/a/nobr')]

    def _get_precedential_statuses(self):
        statuses = []
        for status in self.html.xpath('//table/td[4]/text()'):
            if 'opn' in status.lower():
                statuses.append('Published')
            elif 'sum' in status.lower():
                statuses.append('Unpublished')
            else:
                statuses.append('Unknown')
        return statuses
