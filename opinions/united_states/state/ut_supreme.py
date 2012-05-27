from GenericSite import GenericSite
import re
import time
from datetime import date


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = (
        'http://www.utcourts.gov/opinions/supopin/index.htm')
        self.court_id = self.__module__

    def _get_case_names(self):
        return [name for name in self.html.xpath(
        '/html/body//div[@id="content"]//p[a[@class="bodylink"]]/a/text()')]

    def _get_download_urls(self):
        return [t for t in self.html.
                xpath('/html/body//div[@id="content"]'
                      '//p[a[@class="bodylink"]]/a/@href')]

    def _get_docket_numbers(self):
        docketNumbers = []
        for text in self.html.xpath(
        '/html/body//div[@id="content"]//p[a[@class="bodylink"]]/text()'):
            try:
                parts = text.strip().split(', ')
                docketNumbers.append(parts[1])
            except IndexError:
                continue
        return docketNumbers

    def _get_case_dates(self):
        dates = []
        for text in self.html.xpath('/html/body//div[@id="content"]'
        '//p[a[@class="bodylink"]]/text()'):
            parts = text.strip().split(', ')
            try:
                caseDate = parts[2] + ', ' + parts[3]
                dates.append(date.fromtimestamp(
                time.mktime(time.strptime(caseDate, '%B %d, %Y'))))
            except IndexError:
                continue
        return dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)