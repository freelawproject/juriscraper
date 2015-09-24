# Editor: mlr
# Maintenance log
#    Date     | Issue
# 2013-01-28  | InsanityException due to the court adding busted share links.
# 2014-07-02  | New website required rewrite.

from juriscraper.OpinionSite import OpinionSite
import time
from datetime import date
from juriscraper.lib.string_utils import clean_string


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://media.ca11.uscourts.gov/opinions/pub/logname.php'

    def _get_case_names(self):
        return [e for e in self.html.xpath('//tr/td[1]//text()')]

    def _get_download_urls(self):
        return [e for e in self.html.xpath('//tr/td[1]/a/@href')]

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath('//tr/td[5]//text()'):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(clean_string(date_string), '%m-%d-%Y'))))
        return dates

    def _get_docket_numbers(self):
        return [e for e in self.html.xpath('//tr/td[2]//text()')]

    def _get_precedential_statuses(self):
        if 'unpub' in self.url:
            return ['Unpublished'] * len(self.case_names)
        else:
            return ['Published'] * len(self.case_names)

    def _get_nature_of_suit(self):
        return [e for e in self.html.xpath('//tr/td[4]//text()')]
