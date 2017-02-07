# -*- coding: utf-8 -*-

"""
History:
 - 2014-08-05, mlr: Updated.
 - 2015-06-19, mlr: Updated to simply the XPath expressions and to fix an OB1
   problem that was causing an InsanityError. The cause was nasty HTML in their
   page.
 - 2015-10-20, mlr: Updated due to new page in use.
 - 2015-10-23, mlr: Updated to handle annoying situation.
 - 2016-02-25 arderyp: Updated to catch "ORDER" (in addition to "Order") in download url text
"""
import six

from lxml import html

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string, clean_if_py3


class Site(OpinionSite):
    # Skip first row of table, it's a header
    starting_table_row = '//table//tr[position() > 1]'

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'https://www.isc.idaho.gov/appeals-court/isc_civil'
        self.court_id = self.__module__

    def _download(self, **kwargs):
        # Idaho uses a certificate with a bad chain, so we can't verify it.
        return super(Site, self)._download(request_dict={'verify': False})

    def _get_case_names(self):
        case_names = []
        path = '%s/td[3]' % self.starting_table_row
        for cell in self.html.xpath(path):
            name_string = html.tostring(cell, method='text', encoding='unicode')
            name_string = clean_if_py3(name_string).strip()
            if name_string:
                case_names.append(name_string)
        return case_names

    def _get_download_urls(self):
        # We'll accept an order document if the opinion document
        # is missing. But we obviously prefer the opinion doc,
        # so we put it first in the order below, and we take the
        # first link that matches in path in each 4th cell.
        path = self.starting_table_row + '/td[4]//' \
               '  a[contains(.//text(), "Opinion") or ' \
               '    contains(.//text(), "Order") or ' \
               '    contains(.//text(), "ORDER")][1]/@href'
        return [url for url in self.html.xpath(path)]

    def _get_case_dates(self):
        case_dates = []
        path = '%s/td[1]' % self.starting_table_row
        for cell in self.html.xpath(path):
            date_string = html.tostring(cell, method='text', encoding='unicode')
            date_string = clean_if_py3(date_string).strip()
            if date_string:
                if six.PY2:
                    date_string = date_string.encode('ascii', 'ignore')
                date_string = date_string.replace('Sept ', 'Sep ')  # GIGO!  (+1 by arderyp)
                case_dates.append(convert_date_string(date_string))
        return case_dates

    def _get_docket_numbers(self):
        path = '%s/td[2]//text()' % self.starting_table_row
        return [text.strip() for text in self.html.xpath(path) if text.strip()]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
