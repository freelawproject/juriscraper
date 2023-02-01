"""
Scraper for Pennsylvania Attorney General
CourtID: paag
Court Short Name: Pennsylvania AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
import re
from datetime import datetime as dt

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = (
            "https://www.attorneygeneral.gov/resources/official-ag-opinions/"
        )
        self.year = dt.today().year

    def _process_html(self):
        """Process html

        :return: None
        """
        if self.test_mode_enabled():
            self.year = "2023-01-31"
        for row in self.html.xpath(".//li/a[contains(@href, '.pdf')]"):
            name = row.xpath(".//text()")[0]
            docket = ""
            url = row.xpath(".//@href")[0]
            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": name,
                    "date": str(self.year),
                    "date_filed_is_approximate": True,
                }
            )

    def extract_from_text(self, scraped_text):
        """Extract date from PDF content

        :param scraped_text: PDF content
        :return: Metadata date content for CL
        """
        pattern = re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4})")
        match = pattern.search(scraped_text)
        if match:
            date_filed = dt.strptime(match.group(), "%B %d, %Y").strftime(
                "%Y-%m-%d"
            )
            metadata = {
                "OpinionCluster": {
                    "date_filed": date_filed,
                    "date_filed_is_approximate": False,
                },
            }
            return metadata
