"""Scraper for Supreme Court of Maine
CourtID: me
Court Short Name: Me.
Author: Brian W. Carver
Date created: June 20, 2014
"""

from datetime import date
from datetime import datetime
from lxml import html

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.courts.maine.gov/opinions_orders/supreme/publishedopinions.shtml'

    def _get_download_urls(self):
        path = '//table//tr/td[2]/a/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath('//table//tr/td[2]/a'):
            s = html.tostring(e, method='text', encoding='unicode')
            case_names.append(s)
        return case_names

    def _get_case_dates(self):
        path = '//table//tr/td[3]/text()'
        return [datetime.strptime(date_string, '%B %d, %Y').date()
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_neutral_citations(self):
        path = '//table//tr/td[1]/text()'
        return list(self.html.xpath(path))
