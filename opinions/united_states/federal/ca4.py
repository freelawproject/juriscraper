from juriscraper.GenericSite import GenericSite
import re
import time
from datetime import date

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://pacer.ca4.uscourts.gov/opinions_week.htm'
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for text in self.html.xpath('//a[contains(@href, "opinion.pdf")]/following-sibling::text()[1]'):
            case_names.append(text.split('(')[0].strip())
        return case_names

    def _get_download_urls(self):
        return [e for e in self.html.xpath('//a[contains(@href, "opinion.pdf")]/@href')]

    def _get_case_dates(self):
        date_regex = re.compile('\d{2}/\d{2}/\d{4}')
        dates = []
        for e in self.html.xpath('//a[contains(@href, "opinion.pdf")]/following-sibling::text()'):
            try:
                date_string = date_regex.search(e).group(0)
            except AttributeError:
                # We have to try a bunch of text notes before we'll get the right ones
                continue
            dates.append(date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y'))))
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        # using download link, we can get the docket numbers
        for download_url in self.download_urls:
            fileName = download_url.split('/')[-1]
            docket_number = fileName.split('.')[0]
            # the docket number needs a hyphen inserted after the second digit
            docket_number = docket_number[0:2] + "-" + docket_number[2:]
            docket_numbers.append(docket_number)
        return docket_numbers

    def _get_precedential_statuses(self):
        statuses = []
        # using download link, we can get the statuses
        for download_url in self.download_urls:
            fileName = download_url.split('/')[-1]
            status = fileName.split('.')[1]
            if status.lower() == 'u':
                statuses.append('Unpublished')
            elif status.lower() == 'p':
                statuses.append('Published')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_lower_courts(self):
        '''This is available, but very hard to get consistently, thus punted.'''
        return None

    def _get_lower_court_judges(self):
        '''This is available, but very hard to get consistently, thus punted.'''
        return None

    def _get_dispositions(self):
        '''This is available, but very hard to get consistently, thus punted.'''
        return None

    def _get_judges(self):
        '''This is available, but very hard to get consistently, thus punted.'''
        pass

    def _download_backwards(self):
        '''Note that links of the following form can be constructed:
        http://pacer.ca4.uscourts.gov/dailyopinions/opinions022412.htm'''
        pass
