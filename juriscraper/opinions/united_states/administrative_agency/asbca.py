"""Scraper for Armed Services Board of Contract Appeals
CourtID: asbca
Court Short Name: ASBCA
Author: Jon Andersen
Reviewer: mlr
History:
    2014-09-11: Created by Jon Andersen
    2016-03-17: Website and phone are dead. Scraper disabled in __init__.py.
"""

import re
from datetime import datetime

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string, clean_if_py3


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.asbca.mil/Decisions/decisions%d.html' % datetime.today().year
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
            colname = clean_if_py3(''.join(column.itertext())).strip()
            self.columns[colname] = i
            i += 1
        return self.columns

    def _get_case_dates(self):
        self.parse_column_names()
        path = "//table/tr[td/a]/td[%d]/text()" % (self.columns['Decision Date'])
        return [self._get_date_object_from_string(date_string) for date_string in self.html.xpath(path)]

    def _get_date_object_from_string(self, date_string):
        date_string = clean_if_py3(date_string).strip().replace(' ,', ', ').replace('2104', '2014')
        return convert_date_string(date_string)

    def _get_case_names(self):
        path = "//table/tr/td/a[1]"
        case_names = [clean_if_py3("".join(txt.itertext()).strip())
                      for txt in self.html.xpath(path)]
        return case_names

    def _get_download_urls(self):
        path = "//table/tr/td/a[1]/@href"
        return [clean_if_py3(href).strip() for href in self.html.xpath(path)]

    def _get_judges(self):
        path = "//table/tr[td/a]/td[%d]/text()" % (self.columns['Judge'],)
        return [clean_if_py3(txt).strip() for txt in self.html.xpath(path)]

    def _get_docket_numbers(self):
        if "ASBCA Number" not in self.columns:
            return None
        path = "//table/tr[td/a]/td[%d]/text()" % self.columns['ASBCA Number']
        return [("ASBCA No. " + clean_if_py3(txt).strip()) for txt in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)

    def _download_backwards(self, year):
        self.url = 'http://www.asbca.mil/Decisions/decisions%d.html' % year
        if year == 2010:
            self.url = 'http://www.asbca.mil/Decisions/decisions.html'
        self.html = self._download()

    def _get_case_name_shorts(self):
        # We don't (yet) support short case names for administrative bodies.
        return None
