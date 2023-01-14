"""
Scraper for Massachusetts Land Court
CourtID: massland
Court Short Name: Mass Land Ct
Author: William Palin
Court Contact:
Reviewer:
History:
 - 2020-12-05: Created.
Notes:
 - On Masscases.com they list all the cases on one long page.  A very atypical pattern
"""

import datetime
from typing import List
from urllib.parse import quote

from juriscraper.lib.string_utils import convert_date_string, titlecase
from juriscraper.OpinionSiteLinear import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.masscases.com/land_date.html"
        self.court_id = self.__module__
        self.year = None

    def _get_download_urls(self) -> List[str]:
        links = self.html.xpath(
            f'//*[@id="{self.year}"]/../following-sibling::section/table//tr/td[2]/a'
        )
        return [row.get("href") for row in links]

    def _get_docket_numbers(self) -> List[str]:
        links = self.html.xpath(
            f'//*[@id="{self.year}"]/../following-sibling::section/table//tr/td[2]/a'
        )
        return [row.text for row in links]

    def _get_case_names(self) -> List[str]:
        return [
            titlecase(case_name)
            for case_name in self.html.xpath(
                f'//*[@id="{self.year}"]/../following-sibling::section/table//tr/td[3]/text()'
            )
        ]

    def _get_case_dates(self) -> List[datetime.date]:
        self.year = self.html.xpath('//li[@class="menuitems"]/a/text()')[-1]
        return [
            convert_date_string(
                date_text.replace("AUGUSET", "August").replace(
                    "OCOTBER", "October"
                ),
                fuzzy=True,
            )
            for date_text in self.html.xpath(
                f'//*[@id="{self.year}"]/../following-sibling::section/table//tr/td[1]/text()'
            )
        ]

    def _get_precedential_statuses(self) -> List[str]:
        return len(self.download_urls) * ["Published"]
