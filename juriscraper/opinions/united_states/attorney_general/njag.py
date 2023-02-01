"""
Scraper for New Jersey Attorney General
CourtID: njag
Court Short Name: New Jersey AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://nj.gov/oag/ag-opinions.htm"

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//a[contains(@href, '.pdf')]"):
            if "Register Version" in row.text_content():
                break
            self.cases.append(
                {
                    "url": row.xpath(".//@href")[0],
                    "docket": row.text_content(),
                    "name": f"Unamed Opinion {row.text_content()}",
                    "date": row.text_content().split("-")[0],
                    "date_filed_is_approximate": True,
                }
            )
