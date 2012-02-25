from GenericSite import GenericSite
import time
from datetime import date

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.ca7.uscourts.gov/fdocs/docs.fwx?yr=&num=&Submit=Past+Week&dtype=Opinion&scrid=Select+a+Case'
        self.court_id = self.__module__

    def _get_case_names(self):
        return [e for e in self.html.xpath('//table//table/tr[position() >= 3]/td[2]/text()')]

    def _get_download_links(self):
        return [e for e in self.html.xpath('//table//table/tr[position() >= 3]/td[5]/a/@href')]

    def _get_case_dates(self):
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y')))
                    for date_string in self.html.xpath('//table//table/tr[position() >= 3]/td[4]/text()')]

    def _get_docket_numbers(self):
        return [docket_number for docket_number in
                    self.html.xpath('//table//table/tr[position() >= 3]/td[1]/a/text()')]

    def _get_precedential_statuses(self):
        statuses = []
        for _ in range(0, len(self.case_names)):
            if 'opinion' in self.url.lower():
                statuses.append('Published')
            elif 'nonprecedential' in self.url.lower():
                statuses.append('Unpublished')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_nature_of_suit(self):
        return [nature for nature in self.html.xpath('//table//table/tr[position() >= 3]/td[3]/text()')]
