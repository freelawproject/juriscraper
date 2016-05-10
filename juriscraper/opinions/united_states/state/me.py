"""Scraper for Supreme Court of Maine
CourtID: me
Court Short Name: Me.
Author: Brian W. Carver
Date created: June 20, 2014

History:
  2014-06-25 (est): Added code for additional date formats.
  2014-07-02: Was receiving InsanityException and tweaked date code to get some
              missing dates.
  2014-12-15: Fixes insanity exception by tweaking the XPaths.
"""

from datetime import datetime

from juriscraper.OpinionSite import OpinionSite
from lxml import html


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.courts.maine.gov/opinions_orders/supreme/publishedopinions.shtml'

    def _get_download_urls(self):
        path = '//table//tr/td[2]/a[1]/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath('//table//tr/td[2]/a[1]'):
            s = html.tostring(e, method='text', encoding='unicode')
            case_names.append(s)
        return case_names

    def _get_case_dates(self):
        path = '//table//tr/td[3]/text()'
        date_styles = ['%B %d, %Y', '%B %d,%Y']
        dates = []
        for s in self.html.xpath(path):
            for date_style in date_styles:
                try:
                    d = datetime.strptime(s.strip(), date_style).date()
                except ValueError:
                    continue
                dates.append(d)
        return dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_neutral_citations(self):
        path = '//table[position() > 1]//tr/td[1]//text()'
        return list(self.html.xpath(path))
