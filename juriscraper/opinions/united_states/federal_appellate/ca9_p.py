"""
History:
    - 2014-08-05: Updated by mlr because it was not working, however, in middle
      of update, site appeared to change. At first there were about five
      columns in the table and scraper was failing. Soon, there were seven and
      the scraper started working without my fixing it. Very odd.
"""

import time
from datetime import date

from dateutil.rrule import DAILY, rrule
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase
from lxml import html


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "http://www.ca9.uscourts.gov/opinions/index.php"
        self.base = ('//table[@id = "search-data-table"]//tr['
                     '    not(@id = "c_row_") and '
                     '    not('
                     '        contains(child::td//text(), "NO OPINIONS") or'
                     '        contains(child::td//text(), "No Opinions") or'
                     '        contains(child::td//text(), "NO MEMO") or'
                     '        contains(child::td//text(), "No Memo")'
                     '    )'
                     '][position() > 1]')
        self.court_id = self.__module__
        self.back_scrape_iterable = [i.date() for i in rrule(
            DAILY,
            dtstart=date(2005, 1, 3),
            until=date(2015, 1, 1),
        )]

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
        docket_numbers = []
        for e in self.html.xpath('{}/td[2]'.format(self.base)):
            s = html.tostring(e, method='text', encoding='unicode')
            docket_numbers.append(s)
        return docket_numbers

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
            if t.lower().strip() == 'n/a':
                t = ''
            nos.append(t)
        return nos

    def _get_lower_court(self):
        path = '{base}/td[3]//text()'.format(base=self.base)
        return list(self.html.xpath(path))

    def _download_backwards(self, d):
        self.method = 'POST'
        self.parameters = {
            'c_page_size': '50',
            'c__ff_cms_opinions_case_name_operator': 'like',
            'c__ff_cms_opinions_case_num_operator': 'like',
            'c__ff_cms_opinions_case_origin_operator': 'like',
            'c__ff_cms_opinions_case_origin': 'like',
            'c__ff_j1_name_operator': 'like%25',
            'c__ff_j2_name_operator': 'like%25',
            'c__ff_cms_opinions_case_type_operator': '%3D',
            'c__ff_cms_opinion_date_published_operator': 'like',
            'c__ff_cms_opinion_date_published': d.strftime('%m/%d/%Y'),
            'c__ff_onSUBMIT_FILTER': 'Search'
        }

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
