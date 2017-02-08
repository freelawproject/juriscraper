"""Scraper for the Navy-Marine Corps Court of Criminal Appeals
CourtID: nmcca
Court Short Name:
Reviewer: mlr
History:
    15 Sep 2014: Created by Jon Andersen
"""

from juriscraper.OpinionSite import OpinionSite
import time
from datetime import date
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.jag.navy.mil/courts/opinion_archive.htm'
        self.court_id = self.__module__
        self.back_scrape_iterable = range(2013, 2004-1, -1)

    def _get_case_dates(self):
        path = '//table/tbody/tr/td[3]//text()'
        case_dates = []
        for date_string in self.html.xpath(path):
            # Manually fix broken data
            if date_string == "6/13/30/13":
                date_string = "6/13/13"
            if date_string == "6/11/30/13":
                date_string = "6/11/13"
            if date_string == "02/12/09 & 12/04/08":
                date_string = "02/12/09"
            for date_fmt in ['%m/%d/%Y', '%m/%d/%y']:
                try:
                    d = date.fromtimestamp(
                        time.mktime(time.strptime(date_string, date_fmt)))
                    case_dates.append(d)
                except:
                    pass
        return case_dates

    def _get_case_names(self):
        path = '//table/tbody/tr/td[1]/text()'
        return [titlecase(text) for text in self.html.xpath(path)]

    def _get_download_urls(self):
        path = '//table/tbody/tr/td[4]/a[1]/@href'
        return [e for e in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = '//table/tbody/tr/td[2]//text()'
        return [docket_number for docket_number in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)

    def _download_backwards(self, year):
        self.url = 'http://www.jag.navy.mil/courts/opinion_archive_%d.htm' % year
        self.html = self._download()
