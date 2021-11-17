"""Scraper for the Air Force Court of Criminal Appeals
CourtID: afcca
Court Short Name: Air Force Court of Criminal Appeals
Reviewer: mlr
History:
    15 Sep 2014: Created by Jon Andersen
"""

from datetime import date

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = list(range(2013, 2002 - 1, -1))
        self.url_base = "http://afcca.law.af.mil/content/opinions_date_%d.html"
        self.url = self.url_base % date.today().year
        self.table_cell_path = '//table[@width="800"][@align="center"]/tr[position() > 2]/td[%d]%s'

        # HTTPS certificate is bad, but hopefully they'll fix it and we can remove the line below
        self.disable_certificate_verification()

    def cell_path(self, cell, substring=""):
        return self.table_cell_path % (cell, substring)

    def _get_case_dates(self):
        path = self.cell_path(5)
        return [
            convert_date_string(cell.text_content())
            for cell in self.html.xpath(path)
        ]

    def _get_case_names(self):
        path = self.cell_path(2, "/a")
        return [cell.text_content() for cell in self.html.xpath(path)]

    def _get_download_urls(self):
        path = self.cell_path(2, "/a/@href")
        return [href for href in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = self.cell_path(3)
        return [f"ACM {cell.text_content()}" for cell in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        statuses = []
        path = self.cell_path(4)
        for cell in self.html.xpath(path):
            text = cell.text_content()
            statuses.append(
                "Published" if "Published" in text else "Unpublished"
            )
        return statuses

    def _download_backwards(self, year):
        self.url = self.url_base % year
        self.html = self._download()
