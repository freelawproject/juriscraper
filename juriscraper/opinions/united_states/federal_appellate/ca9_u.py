"""
History:
 - 2014-08-07: Fixed due to InsanityError on docketnumber
"""

import time
from datetime import date

from dateutil.rrule import DAILY, rrule
from lxml import html

from juriscraper.opinions.united_states.federal_appellate import ca9_p


class Site(ca9_p.Site):
    """The unpublished cases have one more column than the published. Thus some
    overriding is done here. More than usual, but it's very slight tweaks."""
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "http://www.ca9.uscourts.gov/memoranda/?o_mode=view&amp;o_sort_field=21&amp;o_sort_type=DESC&o_page_size=100"
        self.court_id = self.__module__
        self.base = ('//table[@id = "c__contentTable"]//tr['
                     '    not(@id = "c_row_") and '
                     '    not('
                     '        contains(child::td//text(), "NO OPINIONS") or'
                     '        contains(child::td//text(), "No Opinions") or'
                     '        contains(child::td//text(), "NO MEMO") or'
                     '        contains(child::td//text(), "No Memo")'
                     '    )'
                     ']')
        self.back_scrape_iterable = [i.date() for i in rrule(
            DAILY,
            dtstart=date(2009, 11, 11),
            until=date(2015, 1, 1),
        )]

    def _get_case_dates(self):
        path = '{base}/td[7]//text()'.format(base=self.base)
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y')))
                    for date_string in self.html.xpath(path)]

    def _get_nature_of_suit(self):
        nos = []
        for e in self.html.xpath('{base}/td[5]'.format(base=self.base)):
            s = html.tostring(e, method='text', encoding='unicode')
            nos.append(s)
        return nos

    def _get_lower_court(self):
        path = '{base}/td[4]//text()'.format(base=self.base)
        return list(self.html.xpath(path))

    def _download_backwards(self, d):
        self.url = 'http://www.ca9.uscourts.gov/memoranda/'
        self.method = 'POST'
        self.parameters = {
            'c_page_size': '50',
            'c__ff_cms_memoranda_case_name_operator': 'like',
            'c__ff_cms_memoranda_case_num_operator': 'like',
            'c__ff_cms_memoranda_case_panel_operator': 'like',
            'c__ff_cms_memoranda_case_origin_operator': 'like',
            'c__ff_cms_memoranda_case_type_operator': '%3D',
            'c__ff_cms_memoranda_filed_date_operator': 'like',
            'c__ff_cms_memoranda_filed_date': d.strftime('%m/%d/%Y'),
            'c__ff_onSUBMIT_FILTER': 'Search'
        }

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
