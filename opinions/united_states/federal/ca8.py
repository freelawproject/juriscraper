from GenericSite import GenericSite
import re
import time
from datetime import date

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.ca8.uscourts.gov/cgi-bin/new/today2.pl'
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        case_name_regex = re.compile('(\d{2}/\d{2}/\d{4})(.*)')
        for text in self.html.xpath('//a[contains(@href, ".pdf")]/following-sibling::b/text()'):
            case_names.append(case_name_regex.search(text).group(2))
        return case_names

    def _get_download_links(self):
        return [e for e in self.html.xpath('//a[contains(@href, ".pdf")]/@href')]

    def _get_case_dates(self):
        case_dates = []
        case_date_regex = re.compile('(\d{2}/\d{2}/\d{4})(.*)')
        for text in self.html.xpath('//a[contains(@href, ".pdf")]/following-sibling::b/text()'):
            date_string = case_date_regex.search(text).group(1)
            case_dates.append(date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y'))))
        return case_dates

    def _get_docket_numbers(self):
        docket_numbers = []
        docket_number_regex = re.compile('(\d{2})(\d{4})(u|p)', re.IGNORECASE)
        for docket_number in self.html.xpath('//a[contains(@href, ".pdf")]/text()'):
            regex_results = docket_number_regex.search(docket_number)
            docket_numbers.append('%s-%s' % (regex_results.group(1), regex_results.group(2)))
        return docket_numbers

    def _get_precedential_statuses(self):
        statuses = []
        for docket_number in self.html.xpath('//a[contains(@href, ".pdf")]/text()'):
            docket_number = docket_number.split('.')[0]
            if 'p' in docket_number.lower():
                statuses.append('Published')
            elif 'u' in docket_number.lower():
                statuses.append('Unpublished')
            else:
                statuses.append('Unknown')
        return statuses
