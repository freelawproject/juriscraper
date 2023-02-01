"""
Scraper for Delaware Attorney General
CourtID: delag
Court Short Name: Delaware AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
import datetime
import re
from typing import Optional

from juriscraper.DeferringList import DeferringList
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = f"https://attorneygeneral.delaware.gov/opinions/"
        self.seeds = []

    def _process_html(self):
        """Process the html

        :return: None
        """
        for row in self.html.xpath(".//h2/a"):
            content = row.text_content()
            pattern = re.compile(r"(\d+-IB\d+) (\d+/\d+/\d+) (.*)")
            match = pattern.search(content)
            docket, date, name = match.groups()
            self.seeds.append(row.xpath("./@href")[0])
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "url": "",
                    "date": date,
                }
            )

    def _get_download_urls(self) -> DeferringList:
        """Get urls using a deferring list.

        :return: Download URLs
        """

        def get_download_url(link: str) -> str:
            """Abstract out the case url from the page.

            :param link: Link to fetch links from
            :return:
            """
            if self.test_mode_enabled():
                return link
            html = self._get_html_tree_by_url(link)
            return html.xpath(".//a[contains(@href, '.pdf')]/@href")[0]

        return DeferringList(seed=self.seeds, fetcher=get_download_url)
