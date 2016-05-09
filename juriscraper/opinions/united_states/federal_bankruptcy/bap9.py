"""Scraper for the United States Bankruptcy Appellate Panel for the Ninth Circuit
CourtID: bap9
Court Short Name: 9th Cir. BAP"""

import time
from datetime import date

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.ca9.uscourts.gov/bap/'
        self.court_id = self.__module__
        self.method = 'POST'
        self.parameters = {
            'c_mode': 'view',
            'c_page_size': '500',
        }

    def _get_case_names(self):
        path = '''//table[3]//tr/td[1]/a/text()'''
        return ["In re: " + titlecase(text) for text in self.html.xpath(path)]

    def _get_download_urls(self):
        path = '''//table[3]//tr/td[1]/a/@href'''
        return [e for e in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        statuses = []
        path = '''//table[3]//tr/td[2]//text()'''
        for txt in self.html.xpath(path):
            if 'Unpublished' in txt:
                statuses.append('Unpublished')
            elif 'Published' in txt:
                statuses.append('Published')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_docket_numbers(self):
        path = '''//table[3]//tr/td[3]//text()'''
        return [docket_number for docket_number in self.html.xpath(path)]

    def _get_case_dates(self):
        path = '''//table[3]//tr/td[4]//text()'''
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y')))
                    for date_string in self.html.xpath(path)]
