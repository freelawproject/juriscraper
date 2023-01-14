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

  2022-01-06: This scraper is not maintained. Future work to gather this
              data should be done by scraping the CourtListener API
              https://www.courtlistener.com/api/rest/v3/clusters/?docket__court__id=me
"""

from lxml import html

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.courts.maine.gov/courts/sjc/opinions.html"
        self.path_root = '//table[contains(.//th[1], "Opinion")]'

    def _get_cell_path(self, cell_number: int, subpath: str = "") -> str:
        path = '//table[contains(.//th[1], "Opinion")]//td[%d]'
        return f"{path}/{subpath}" if subpath else path

    def _get_download_urls(self):
        path = f"{self.path_root}//td[2]/a[1]/@href"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        case_names = []
        path = f"{self.path_root}//td[2]/a[1]"
        for e in self.html.xpath(path):
            s = html.tostring(e, method="text", encoding="unicode")
            case_names.append(s)
        return case_names

    def _get_case_dates(self):
        dates = []
        path = f"{self.path_root}//td[3]"
        for cell in self.html.xpath(path):
            date_string = cell.text_content().replace("Aguust", "August")
            dates.append(convert_date_string(date_string))
        return dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_citations(self):
        path = f"{self.path_root}//td[1]//text()"
        return list(self.html.xpath(path))
