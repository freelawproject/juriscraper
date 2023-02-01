"""
Scraper for Georgia Attorney General
CourtID: gaag
Court Short Name: Georgia AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
import datetime
from typing import Optional

from lxml import html

from juriscraper.DeferringList import DeferringList
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://law.georgia.gov/opinions/official"
        self.seeds = []

    def _process_html(self):
        """Process the html

        :return: None
        """
        for row in self.html.xpath(".//tbody/tr"):
            url = row.xpath(".//a/@href")[0]
            docket = row.xpath(".//a/text()")[0]
            summary = row.xpath(".//td[2]")[0].text_content()
            self.seeds.append(url)
            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": f"Official Opinion {docket}",
                    "summary": f"In re: {summary}",
                    "date": docket.split("-")[0],
                }
            )

    def _get_case_dates(self) -> DeferringList:
        """Get case names using a deferring list.

        :return: Deferring List
        """

        def get_case_date(link: str) -> Optional[datetime.date]:
            """Abstract out the case date from the case page."""
            if self.test_mode_enabled():
                return datetime.datetime.strptime(
                    "2022-01-01", "%Y-%m-%d"
                ).date()
            html = self._get_html_tree_by_url(link)
            date_str = html.xpath(".//div/time/text()")[0]
            try:
                return datetime.datetime.strptime(date_str, "%B %d, %Y").date()
            except ValueError:
                pass

        return DeferringList(seed=self.seeds, fetcher=get_case_date)

    @staticmethod
    def cleanup_content(content) -> str:
        """Process the HTML into content because PDF doesnt exist

        :param content: HTML page
        :return: Cleaned HTML content
        """
        tree = html.fromstring(content)
        core_elements = tree.xpath(
            ".//div[contains(./@class, 'page-top--opinion')] | .//div[contains(./@class, 'body-content--offset')]"
        )
        opinion = []
        for el in core_elements:
            content = (el.text or "") + "".join(
                [
                    html.tostring(child, pretty_print=True, encoding="unicode")
                    for child in el.iterchildren()
                ]
            )
            opinion.append(content)
        return "".join(opinion)
