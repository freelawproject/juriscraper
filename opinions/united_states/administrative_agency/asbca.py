"""Scraper for Armed Services Board of Contract Appeals
CourtID: asbca
Court Short Name: ASBCA
Author: Jon Andersen
Reviewer: mlr
History:
    2014-09-11: Created by Jon Andersen
"""

from datetime import datetime
import re

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.asbca.mil/Decisions/decisions%d.html' \
                   % datetime.today().year
        self.columns = None
        self.back_scrape_iterable = range(2013, 2000 - 1, -1)

    # Fix broken month names and funky whitespace usage.
    def _clean_text(self, text):
        text = super(Site, self)._clean_text(text)
        text = text.replace('&#160;', ' ').replace('&nbsp;', ' ')
        text = text.replace("Januray", "January")
        text = text.replace("Februrary", "February")
        text = re.sub(re.compile(r"[\s]+", flags=re.MULTILINE), " ", text)
        return text

    def parse_column_names(self):
        # Lookup column names and save them for later
        self.columns = dict()
        path = "//table/tr[1]/td"
        i = 1
        for column in self.html.xpath(path):
            colname = "".join(column.itertext()).strip()
            self.columns[colname] = i
            i += 1
        return self.columns

    def _get_case_dates(self):
        self.parse_column_names()
        path = "//table/tr[td/a]/td[%d]/text()" \
               % (self.columns['Decision Date'])

        def sanitize_date(s):
            return s.strip().replace(' ,', ', ').replace('2104', '2014')
        return [datetime.strptime(sanitize_date(date_string), '%B %d, %Y').date()
                for date_string in self.html.xpath(path)]

    def _get_case_names(self):
        path = "//table/tr/td/a[1]"
        case_names = ["".join(txt.itertext()).strip()
                      for txt in self.html.xpath(path)]
        return case_names

    def _get_download_urls(self):
        path = "//table/tr/td/a[1]/@href"
        return [href.strip() for href in self.html.xpath(path)]

    def _get_judges(self):
        path = "//table/tr[td/a]/td[%d]/text()" \
               % (self.columns['Judge'],)
        return [txt.strip() for txt in self.html.xpath(path)]

    def _get_docket_numbers(self):
        if ("ASBCA Number" not in self.columns):
            return None
        path = "//table/tr[td/a]/td[%d]/text()" % self.columns['ASBCA Number']
        return [("ASBCA No. " + txt) for txt in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)

    def _download_backwards(self, year):
        self.url = 'http://www.asbca.mil/Decisions/decisions%d.html' % year
        if (year == 2010):
            self.url = 'http://www.asbca.mil/Decisions/decisions.html'
        self.html = self._download()
