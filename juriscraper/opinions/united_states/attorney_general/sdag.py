"""
Scraper for South Dakota Attorney General
CourtID: sdag
Court Short Name: SD AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
import re
from datetime import datetime
from typing import Optional

from juriscraper.DeferringList import DeferringList
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://atg.sd.gov/OurOffice/OfficialOpinions/opinions.aspx#gsc.tab=0"
        self.seeds = []

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(
            ".//tr/td/a[contains(@href, '.pdf')]/../.."
        ):
            docket = row.xpath(".//td")[0].text_content()
            name = row.xpath(".//td")[1].text_content()
            url = row.xpath(".//td/a/@href")[1]
            self.seeds.append(row.xpath(".//td/a/@href")[0])
            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": name,
                }
            )

    def _get_case_dates(self) -> DeferringList:
        """Get case dates using a deferring list.

        :return: Case dates
        """

        def get_case_date(link: str) -> Optional[datetime.date]:
            """Abstract out the case date from the case page."""
            if self.test_mode_enabled():
                return datetime.strptime("August 17, 2022", "%B %d, %Y").date()
            html = self._get_html_tree_by_url(link)
            date = html.xpath(".//span[@id='lbl_HTML']/p/text()")[0].strip()
            dt = datetime.strptime(date, "%B %d, %Y")
            return dt.date()

        return DeferringList(seed=self.seeds, fetcher=get_case_date)
