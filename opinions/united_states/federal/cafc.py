from juriscraper.GenericSite import GenericSite
import time
from datetime import date

from juriscraper.lib.string_utils import clean_string, titlecase


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.cafc.uscourts.gov/opinions-orders/7/all'
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for case_string in self.html.xpath('//table[@id = "searchResults"]/tr[position() >= 3]/td[4]/a/text()'):
            # Takes care of things like [ERRATA] that are often on the end of 
            # case names.
            case_names.append(titlecase(case_string.split('[')[0]))
        return case_names

    def _get_download_urls(self):
        return [e for e in self.html.xpath('//table[@id = "searchResults"]/tr[position() >= 3]/td[4]/a/@href')]

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath('//table[@id = "searchResults"]/tr[position() >= 3]/td[1]/text()'):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(clean_string(date_string), '%Y-%m-%d'))))
        return dates

    def _get_docket_numbers(self):
        return [e.split('|')[0] for e in self.html.xpath('//table[@id = "searchResults"]/tr[position() >= 3]/td[2]/text()')]

    def _get_precedential_statuses(self):
        statuses = []
        for status in self.html.xpath('//table[@id = "searchResults"]/tr[position() >= 3]/td[5]/text()'):
            if 'nonprecedential' in status.lower():
                statuses.append('Unpublished')
            elif 'precedential' in status.lower():
                statuses.append('Published')
            else:
                statuses.append('Unknown')
        return statuses

    def _download_backwards(self, page):
        # Sample URLs for page 2 and 3 (as of 2011-02-09)
        # http://www.cafc.uscourts.gov/opinions-orders/0/50/all/page-11-5.html
        # http://www.cafc.uscourts.gov/opinions-orders/0/100/all/page-21-5.html
        if page == 0:
            self.url = "http://www.cafc.uscourts.gov/opinions-orders/0/all"
        else:
            self.url = "http://www.cafc.uscourts.gov/opinions-orders/0/%s/all/page-%s1-5.html" % ((page * 50), page)
        self.html = self._download()
