from juriscraper.GenericSite import GenericSite
import time
from datetime import date

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.ca6.uscourts.gov/cgi-bin/opinions.pl'
        self.method = 'POST'
        self.parameters = {
                'CASENUM' : '',
                'TITLE' : '',
                'FROMDATE' : date.strftime(date.today(), '%m/%d/%Y'),
                'TODATE' : date.strftime(date.today(), '%m/%d/%Y'),
                'OPINNUM' : ''
                }
        self.court_id = self.__module__

    def _get_case_names(self):
        return [e for e in self.html.xpath('//table/tr/td[4]/text()[1]')]

    def _get_download_urls(self):
        return [e for e in self.html.xpath('//table/tr/td[1]/a/@href')]

    def _get_case_dates(self):
        dates = []
        for text_string in self.html.xpath('//table/tr/td[3]/text()'):
            date_string = text_string.strip()
            dates.append(date.fromtimestamp(time.mktime(time.strptime(date_string, '%Y/%m/%d'))))
        return dates

    def _get_docket_numbers(self):
        return [num.strip() for num in self.html.xpath('//table/tr/td[2]/a/text()')]

    def _get_precedential_statuses(self):
        statuses = []
        for filename in self.html.xpath('//table/tr/td[1]/a/text()'):
            if 'n' in filename.lower():
                statuses.append('Unpublished')
            elif 'p' in filename.lower():
                statuses.append('Published')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_lower_courts(self):
        return [text for text in self.html.xpath('//table/tr/td[4]/font/text()')]
