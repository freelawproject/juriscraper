# Author: Brian W. Carver
# Date created: April 12, 2013

# import re
import time
from datetime import date
from lxml import html

from juriscraper.GenericSite import GenericSite
from juriscraper.lib.string_utils import titlecase


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.azcourts.gov/opinions/SearchOpinions.aspx?court=999'

    def _get_download_urls(self):
        path = '//*[contains(@id, "hypCaseNum")]/@href'
        return [t for t in self.html.xpath(path)]

    def _get_case_names(self):
        path = '//*[contains(@id, "lblTitle")]//text()'
        return [titlecase(t.upper()) for t in self.html.xpath(path)]

    def _get_case_dates(self):
        path = '//*[contains(@id, "FilingDate")]//text()'
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y')))
                    for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        statuses = []
        path = '//*[contains(@id, "DecType")]/text()'
        for s in self.html.xpath(path):
            if 'OPINION' in s:
                statuses.append('Published')
            elif 'MEMORANDUM' in s:
                statuses.append('Unpublished')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_docket_numbers(self):
        path = '//*[contains(@id, "hypCaseNum")]//text()'
        return [t for t in self.html.xpath(path)]

    def _get_judges(self):
        path = '//*[contains(@id, "Summary")]/td[2]/text()[1]'
        return [t for t in self.html.xpath(path)]