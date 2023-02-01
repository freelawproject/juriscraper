"""
Scraper for Arkansas Attorney General
CourtID: arkag
Court Short Name: Arkansas AG
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
        self.url = "https://ag-opinions.ark.org/?type=recent&q=90"
        self.seeds = []

    def _process_html(self):
        """Process the html

        :return: None
        """
        for row in self.html.xpath(".//div[@class='card']"):
            name = row.xpath(".//h5/text()")[0]
            url = row.xpath(".//a[contains(@href, '.pdf')]/@href")[0]
            html_url = row.xpath(".//a[contains(@href, '.html')]/@href")[0]
            docket = re.sub(r"\r\n", "", name.split()[1])
            self.seeds.append(html_url)
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "url": url,
                    "summary": row.xpath(".//p/text()")[0],
                    "date": "",
                }
            )

    def _get_case_dates(self) -> DeferringList:
        """Get case names using a deferring list."""

        def get_case_date(link: str) -> Optional[datetime.date]:
            """Abstract out the case date from the case page."""
            if self.test_mode_enabled():
                return datetime.datetime.strptime(
                    "2022-01-01", "%Y-%m-%d"
                ).date()
            html = self._get_html_tree_by_url(link)
            for p in html.xpath(".//p"):
                try:
                    dt = datetime.datetime.strptime(
                        p.text_content(), "%B %d, %Y"
                    )
                    return dt.date()
                except ValueError:
                    pass

        return DeferringList(seed=self.seeds, fetcher=get_case_date)
