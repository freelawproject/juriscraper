"""
History:
    - 2014-08-05: Updated by mlr because it was not working, however, in middle
      of update, site appeared to change. At first there were about five
      columns in the table and scraper was failing. Soon, there were seven and
      the scraper started working without my fixing it. Very odd.
"""

import time
from datetime import date

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase
from lxml import html


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = "http://www.ca9.uscourts.gov/opinions/index.php"
        self.base = ('//table[@id = "c__contentTable"]//tr[not(@id="c_row_") and '
                     'not(contains(child::td//text(), "NO OPINIONS") or'
                     ' contains(child::td//text(), "NO MEMO"))]')
        self.court_id = self.__module__

    def _get_case_names(self):
        path = '{base}/td[1]/a/text()'.format(base=self.base)
        return [titlecase(text) for text in self.html.xpath(path)]

    def _get_download_urls(self):
        path = '{base}/td[1]/a/@href'.format(base=self.base)
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = '{base}/td[7]//text()'.format(base=self.base)
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y')))
                for date_string in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = '{base}/td[2]//text()'.format(base=self.base)
        return list(self.html.xpath(path))

    def _get_precedential_statuses(self):
        statuses = []
        for _ in range(0, len(self.case_names)):
            if 'opinion' in self.url.lower():
                statuses.append('Published')
            elif 'memoranda' in self.url.lower():
                statuses.append('Unpublished')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_nature_of_suit(self):
        path = '{base}/td[5]'.format(base=self.base)
        nos = []
        for e in self.html.xpath(path):
            t = html.tostring(e, method='text', encoding='unicode')
            nos.append(t)
        return nos

    def _get_lower_court(self):
        path = '{base}/td[3]//text()'.format(base=self.base)
        return list(self.html.xpath(path))
