from juriscraper.GenericSite import GenericSite
import re
import time
from datetime import date


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.utcourts.gov/opinions/supopin/index.htm'
        self.court_id = self.__module__

    def _get_case_names(self):
        return [name for name in self.html.xpath('/html/body//div[@id="content"]//p[a[@class="bodylink"]]/a/text()')]

    def _get_download_urls(self):
        return [t for t in self.html.xpath('/html/body//div[@id="content"]//p[a[@class="bodylink"]]/a/@href')]

    def _get_docket_numbers(self):
        docket_numbers = []
        for text in self.html.xpath('/html/body//div[@id="content"]//p[a[@class="bodylink"]]/text()'):
            try:
                parts = text.strip().split(', ')
                docket_numbers.append(parts[1])
            except IndexError:
                # Happens in whitespace-only text nodes.
                continue
        return docket_numbers

    def _get_case_dates(self):
        dates = []
        for text in self.html.xpath('/html/body//div[@id="content"]//p[a[@class="bodylink"]]/text()'):
            parts = text.strip().split(', ')
            try:
                caseDate = parts[2] + ', ' + parts[3]
                dates.append(date.fromtimestamp(
                time.mktime(time.strptime(caseDate, '%B %d, %Y'))))
            except IndexError:
                # Happens in whitespace-only text nodes.
                continue
        return dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_neutral_citations(self):
        neutral_citations = []
        for text in self.html.xpath('/html/body//div[@id="content"]//p[a[@class="bodylink"]]/text()'):
            try:
                parts = text.strip().split(', ')
                neutral_citations.append(parts[4])
            except IndexError:
                # Happens in whitespace-only text nodes.
                continue
        return neutral_citations
