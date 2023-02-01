"""
Scraper for New Jersey Attorney General
CourtID: njag
Court Short Name: New Jersey AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
import datetime
import re

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
            if self.test_mode_enabled():
                date = "2023-01-31"
            else:
                date = re.findall(r"\d{4}", row.text_content())[0]
            self.cases.append(
                {
                    "url": row.xpath(".//@href")[0],
                    "docket": row.text_content(),
                    "name": f"Unamed Opinion {row.text_content()}",
                    "date": date,
                    "date_filed_is_approximate": True,
                }
            )

    def extract_from_text(self, scraped_text):
        """Extract date from downloaded content

        :param scraped_text: Scraped content
        :return: Opinion cluster date filed metadata
        """
        pattern = re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4})")
        match = pattern.search(scraped_text)
        if match:
            date_filed = datetime.datetime.strptime(
                match.group(), "%B %d, %Y"
            ).strftime("%Y-%m-%d")
            metadata = {
                "OpinionCluster": {
                    "date_filed": date_filed,
                    "date_filed_is_approximate": False,
                },
            }
            return metadata
