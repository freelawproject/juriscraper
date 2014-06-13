# Scraper for the United States Court of Appeals for the Seventh Circuit
# CourtID: ca7
# Court Short Name: 7th Cir.

from juriscraper.OpinionSite import OpinionSite
import time
from datetime import date
from lxml import html


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        # The string 'week' can be changed to 'today' to get just today's
        # opinions
        self.url = 'http://media.ca7.uscourts.gov/cgi-bin/rssExec.pl?Time=week&Submit=Submit'
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath('//table//table/tr[position() >= 3]/td[2]'):
            s = html.tostring(e, method='text', encoding='unicode')
            case_names.append(s)
        return case_names

    def _get_download_urls(self):
        return [e for e in self.html.xpath('//table[2]/tr/td/table/tr[position() >=3]/td/a/@href')]

    def _get_case_dates(self):
        return [date.fromtimestamp(time.mktime(time.strptime(date_string.strip(), '%m/%d/%Y')))
                    for date_string in self.html.xpath('//table//table/tr[position() >= 3]/td[4]/text()')]

    def _get_docket_numbers(self):
        return [docket_number for docket_number in
                    self.html.xpath('//table//table/tr[position() >= 3]/td[1]/text()')]

    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath('//table//table/tr[position() >= 3]/td[5]/a'):
            s = html.tostring(e, method='text', encoding='unicode')
            if 'Opinion' in s:
                statuses.append('Published')
            elif 'Nonprecedential' in s:
                statuses.append('Unpublished')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_nature_of_suit(self):
        natures = []
        for e in self.html.xpath('//table//table/tr[position() >= 3]/td[3]'):
            s = html.tostring(e, method='text', encoding='unicode')
            natures.append(s)
        return natures
