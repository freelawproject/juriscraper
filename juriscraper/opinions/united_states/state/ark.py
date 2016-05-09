# Author: Krist Jin
# Reviewer: Michael Lissner
# Date created: 2013-08-03

from datetime import datetime
from lxml import html

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://opinions.aoc.arkansas.gov/weblink8/Browse.aspx?startid=40626'

    def _get_download_urls(self):
        path = '//*[@class="DocumentBrowserNameLink"][../../*[4]//text()]/@href'
        return [t for t in self.html.xpath(path)]

    def _get_case_names(self):
        path = '//*[@class="DocumentBrowserNameLink"][../../*[4]//text()]/nobr/span[1]/text()'
        return [t for t in self.html.xpath(path)]

    def _get_case_dates(self):
        path = '//tr/td[@class="DocumentBrowserCell"][5][../*[4]//text()]//nobr/text()'
        return [datetime.strptime(date_string, '%m/%d/%Y').date()
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//tr/td[@class="DocumentBrowserCell"][4][../*[4]//text()]//nobr'):
            s = html.tostring(e, method='text', encoding='unicode')
            docket_numbers.append(s)
        return docket_numbers

    def _get_judges(self):
        path = '//tr/td[@class="DocumentBrowserCell"][2][../*[4]//text()]//nobr/text()'
        return [titlecase(t.upper()) for t in self.html.xpath(path)]

    def _get_neutral_citations(self):
        path = '//tr/td[@class="DocumentBrowserCell"][6][../*[4]//text()]//nobr/text()'
        return list(self.html.xpath(path))

    def _get_dispositions(self):
        docket_numbers = []
        for e in self.html.xpath('//tr/td[@class="DocumentBrowserCell"][8][../*[4]//text()]//nobr'):
            s = html.tostring(e, method='text', encoding='unicode')
            docket_numbers.append(titlecase(s))
        return docket_numbers


