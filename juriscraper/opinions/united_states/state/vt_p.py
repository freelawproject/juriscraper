"""Scraper for the Supreme Court of Vermont
CourtID: vt
Court Short Name: VT
Court Contact: submit form here https://www.vermontjudiciary.org/website-feedback-form
Author: Brian W. Carver
Date created: 18 Aug 2013
Reviewer: Mike Lissner

If there are errors with the site, you can contact:

 Monica Bombard
 (802) 828-4784

She's very responsive.
"""

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'https://www.vermontjudiciary.org/LC/SupCrtPublish.aspx'

        # Limit number of cases extracted. Number of cases
        # pulled may not match this number exactly since
        # funky html table has some rows that we ignore
        self.max_cases = 100

    def get_cell_base_path(self, index):
        pattern = "//div[@id='WebPartWPQ2']//tr[position() < %d]/td[%d]"
        return pattern % (self.max_cases, index)

    def _get_download_urls(self):
        path = "%s/a[contains(@href, 'pdf')]/@href" % self.get_cell_base_path(1)
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = "%s//text()" % self.get_cell_base_path(2)
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = "%s//text()" % self.get_cell_base_path(5)
        return [convert_date_string(s) for s in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "%s//text()" % self.get_cell_base_path(4)
        return list(self.html.xpath(path))

    def _get_neutral_citations(self):
        path = "%s//text()" % self.get_cell_base_path(3)
        return list(self.html.xpath(path))
