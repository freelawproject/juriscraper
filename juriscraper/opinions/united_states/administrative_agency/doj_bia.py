"""Scraper for Dept of Justice. Board of Immigration Appeals
CourtID: doj_bia
Court Short Name: Dept of Justice. Board of Immigration Appeals
Author: William Palin
Reviewer:
Type:
History:
    2021-12-18: Created by William Palin, Esq.
"""

import re
from datetime import datetime
from typing import List

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.justice.gov/eoir/ag-bia-decisions"
        self.article = None

    def _download(self, request_dict={}):
        html = super()._download(request_dict)
        self.url = html.xpath(".//table//tbody/tr/td/a/@href")[0]
        return self._get_html_tree_by_url(self.url)

    def _get_case_dates(self):
        """Get the case dates for the current page"""
        dates = []
        cites = self.html.xpath("//article")[0].xpath(
            ".//strong[1]/./../text() | .//b[1]/./../text()"
        )
        cites = [c.strip(" ,") for c in cites if c.strip(" ,")]
        for cite in cites:
            year = re.findall("\d{4}", cite)[0]
            dates.append(datetime.strptime(f"{year}-07-01", "%Y-%m-%d").date())
        return dates

    def _get_case_names(self):
        strong = self.html.xpath("//article")[0].xpath(
            ".//strong[1]/text() | .//b[1]/text()"
        )
        return strong

    def _get_docket_numbers(self) -> List[str]:
        """"""
        return self.html.xpath("//article")[0].xpath(
            ".//td[@class='rteright']/a[1]/text()"
        )

    def _get_precedential_statuses(self):
        """"""
        return ["Unpublished"] * len(self.download_urls)

    def _get_download_urls(self):
        """"""
        return self.html.xpath("//article")[0].xpath(
            ".//td[@class='rteright']/a[1]/@href"
        )

    def _get_west_citations(self):
        """"""
        cites = self.html.xpath("//article")[0].xpath(
            ".//strong[1]/./../text() | .//b[1]/./../text()"
        )
        cites = [c.strip(" ,") for c in cites if c.strip(" ,")]
        return cites

    def _get_date_filed_is_approximate(self):
        return [True] * len(self.download_urls)
