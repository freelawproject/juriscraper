# -*- coding: utf-8 -*-

"""
History:
 - 2014-08-05, mlr: Updated.
 - 2015-06-19, mlr: Updated to simply the XPath expressions and to fix an OB1
   problem that was causing an InsanityError. The cause was nasty HTML in their
   page.
 - 2015-10-20, mlr: Updated due to new page in use.
 - 2015-10-23, mlr: Updated to handle annoying situation.
"""

from juriscraper.OpinionSite import OpinionSite
from lxml import html

from datetime import datetime


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.isc.idaho.gov/appeals-court/isc_civil'
        self.court_id = self.__module__

    def _get_case_names(self):
        path = '//table//tr[position() > 1]/td[3]'
        case_names = []
        for e in self.html.xpath(path):
            s = html.tostring(e, method='text', encoding='unicode').strip()
            if s.strip():
                case_names.append(s)
        return case_names

    def _get_download_urls(self):
        path = '//table//tr[position() > 1]/td[4]//' \
               '  a[contains(.//text(), "Opinion") or ' \
               '    contains(.//text(), "Order")]/@href'
        return [s for s in self.html.xpath(path)]

    def _get_case_dates(self):
        path = '//table//tr[position() > 1]/td[1]'
        case_dates = []
        for e in self.html.xpath(path):
            s = html.tostring(e, method='text', encoding='unicode').strip()
            if not s:
                # No content. Press on."
                continue
            s = s.replace('Sept', 'Sep')  # GIGO!
            date_formats = ['%B %d, %Y',
                            '%B %d %Y',
                            '%b %d, %Y',
                            '%b %d %Y']
            for date_format in date_formats:
                try:
                    case_date = datetime.strptime(s, date_format).date()
                    break
                except ValueError:
                    continue
            case_dates.append(case_date)
        return case_dates

    def _get_docket_numbers(self):
        path = '//table//tr[position() > 1]/td[2]//text()'
        docket_numbers = []
        for s in self.html.xpath(path):
            if s.strip():
                docket_numbers.append(s)
        return docket_numbers

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
