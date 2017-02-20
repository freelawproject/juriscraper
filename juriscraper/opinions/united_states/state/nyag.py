"""Scraper for the California Attorney General
CourtID: nyag
Court Short Name: New York Attorney General
"""

import datetime

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = datetime.date.today().year
        self.base_url = 'https://ag.ny.gov/appeals-and-opinions/numerical-index?field_opinion_year_value=%d'
        self.url = self.base_url % self.year
        self.back_scrape_iterable = range(1995, self.year + 1)
        self.row_path = False
        self.cell_path = False
        self.set_paths()

    def _download(self, request_dict={}):
        html = super(Site, self)._download(request_dict)
        if self.method == 'LOCAL':
            # Make sure the year-table you want to test is first in example file
            self.year = int(html.xpath('//table[1]/caption')[0].text_content())
            self.set_paths()
        return html

    def _get_case_dates(self):
        """All we have are years, so estimate middle most day of year"""
        today = datetime.date.today()
        middle_of_year = convert_date_string('July 2, %d' % self.year)
        if self.year == today.year:
            # Not a backscraper, assume cases were filed on day scraped.
            return [today] * len(self.html.xpath(self.row_path))
        else:
            return [middle_of_year] * len(self.html.xpath(self.row_path))

    def _get_case_names(self):
        """No case names available"""
        return ["Untitled New York Attorney General Opinion"] * len(self.case_dates)

    def _get_download_urls(self):
        path = '%s//a/@href' % (self.cell_path % 4)
        return [href for href in self.html.xpath(path)]

    def _get_docket_numbers(self):
        return [cell.text_content().strip() for cell in self.html.xpath(self.cell_path % 1)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)

    def _get_summaries(self):
        """Use Abstract column value"""
        return [cell.text_content().strip() for cell in self.html.xpath(self.cell_path % 2)]

    def _get_date_filed_is_approximate(self):
        return [True] * len(self.case_dates)

    def _download_backwards(self, year):
        self.year = year
        self.url = self.base_url % self.year
        self.set_paths()
        self.html = self._download()

    def set_paths(self):
        self.row_path = '//table[contains(caption, "%d")]/tbody/tr' % self.year
        self.cell_path = self.row_path + '/td[%d]'
