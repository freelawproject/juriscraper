"""Oral Argument Audio Scraper for Eighth Circuit Court of Appeals
CourtID: ca8
Court Short Name: 8th Cir.
Author: Brian W. Carver
Date created: 2014-06-21
"""

from datetime import datetime
from lxml import html

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://8cc-www.ca8.uscourts.gov/circ8rss.xml'

    def _get_download_urls(self):
        download_urls = []
        for e in self.html.xpath('//item/link'):
            url = html.tostring(e, method='text', encoding='unicode')
            download_urls.append(url)
        return download_urls

    def _get_case_names(self):
        case_names = []
        for txt in self.html.xpath('//item/title/text()'):
            case_name = txt.split(': ', 1)[1]
            case_names.append(case_name)
        return case_names

    def _get_case_dates(self):
        case_dates = []
        for txt in self.html.xpath('//item/description/text()'):
            # I can't see it, but there's apparently whitespace or a newline
            # at the end of these dates that has to be removed or we error out.
            case_date = txt.split('about ', 1)[1].strip()
            case_dates.append(datetime.strptime(case_date, '%m-%d-%Y').date())
        return case_dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for txt in self.html.xpath('//item/title/text()'):
            docket_number = txt.split(': ', 1)[0]
            docket_numbers.append(docket_number)
        return docket_numbers
