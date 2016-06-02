# Author: Michael Lissner
# Date created: 2013-05-23

# import re
import time
from datetime import date
from lxml import html

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.courts.state.hi.us/opinions_and_orders/opinions/%s/index.html' % date.today().year
        self.back_scrape_iterable = range(2010, 2013)
        self.court_id = self.__module__

    def _get_download_urls(self):
        path = '//table[@class = "opinionsdata"]/tr/td[3][../td/text() = "S.Ct"][not(contains(../td[3]/a/text(), "Bar"))]/a[1]/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        # There is often a missing link in a case, thus we need an extra check here.
        path = '//table[@class = "opinionsdata"]/tr/td[4][../td/a][../td/text() = "S.Ct"][not(contains(../td[3]/a/text(), "Bar"))]/p[1]/text()[1]'
        case_names = []
        for s in self.html.xpath(path):
            case_names.append(s.split('(')[0])
        return case_names

    def _get_case_dates(self):
        path = '//table[@class = "opinionsdata"]/tr/td[1][../td/a][../td/text() = "S.Ct"][not(contains(../td[3]/a/text(), "Bar"))]/text()'
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y')))
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//table[@class = "opinionsdata"]/tr/td[3][../td/a][../td/text() = "S.Ct"][not(contains(../td[3]/a/text(), "Bar"))]/a[1]/text()'
        return list(self.html.xpath(path))

    def _get_lower_courts(self):
        path = '//table[@class = "opinionsdata"]/tr/td[5][../td/a][../td/text() = "S.Ct"][not(contains(../td[3]/a/text(), "Bar"))]'
        lower_courts = []
        for e in self.html.xpath(path):
            lower_courts.append(html.tostring(e, method='text', encoding='unicode'))
        return lower_courts

    def _download_backwards(self, year):
        self.url = 'http://www.courts.state.hi.us/opinions_and_orders/opinions/%s/index.html' % year
        self.html = self._download()
