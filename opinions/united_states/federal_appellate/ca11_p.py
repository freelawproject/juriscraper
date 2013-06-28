# Editor: mlr
# Maintenance log
#    Date     | Issue
# 2013-01-28  | InsanityException due to the court adding busted share links.

from juriscraper.GenericSite import GenericSite
import time
from datetime import date
from juriscraper.lib.string_utils import clean_string


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.ca11.uscourts.gov/opinions/searchdate.php'
        self.method = 'POST'
        self.parameters = {
                'date'  : time.strftime('%Y-%m', date.today().timetuple()),
            }
        self.court_id = self.__module__

    def _get_case_names(self):
        return [e for e in self.html.xpath('//table//table//table[position() >= 2]/tr[6]/td[2]/text()')]

    def _get_download_urls(self):
        return [e for e in self.html.xpath('//table//table//table[position() >= 2]/tr[3]/td[2]/a[1]/@href')]

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath('//table//table//table[position() >= 2]/tr[4]/td[2]/text()'):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(clean_string(date_string), '%m-%d-%Y'))))
        return dates

    def _get_docket_numbers(self):
        return [e for e in self.html.xpath('//table//table//table[position() >= 2]/tr[1]/td[2]/text()')]

    def _get_precedential_statuses(self):
        statuses = []
        for _ in range(0, len(self.case_names)):
            if 'opinions' in self.url:
                statuses.append('Published')
            elif 'unpub' in self.url:
                statuses.append('Unpublished')
        return statuses

    def _get_nature_of_suit(self):
        return [e for e in self.html.xpath('//table//table//table[position() >= 2]/tr[5]/td[2]//text()')]

    def _download_backwards(self):
        # This link will give you EVERYTHING on a single page: http://www.ca11.uscourts.gov/unpub/searchdate.php
        # This one too: http://www.ca11.uscourts.gov/opinions/searchdate.php
        pass
