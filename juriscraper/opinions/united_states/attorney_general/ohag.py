"""
Scraper for North Dakota Attorney General
CourtID: ndag
Court Short Name: North Dakota AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
from datetime import datetime as dt

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://www.ohioattorneygeneral.gov/About-AG/Service-Divisions/Opinions"

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//h2/a[contains(@href, '.aspx')]/.."):
            url = row.xpath(".//a/@href")[0]
            docket = row.xpath(".//a/text()")[0]
            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": f"Opinion No. {docket}",
                    "date": docket.split("-")[0],
                }
            )

    def extract_from_text(self, scraped_text):
        """"""
        date_str = scraped_text.split("\n")[0]
        date_filed = dt.strptime(date_str, "%B %d, %Y").strftime("%Y-%m-%d")
        metadata = {
            "OpinionCluster": {"date_filed": date_filed},
        }
        return metadata
