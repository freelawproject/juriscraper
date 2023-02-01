"""
Scraper for Conn. Attorney General
CourtID: connag
Court Short Name: Connecticut AG
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
        self.year = datetime.date.today().year
        self.url = (
            f"https://portal.ct.gov/AG/Opinions/{self.year}-Formal-Opinions"
        )

    def _process_html(self):
        """Process the html

        :return: None
        """
        for row in self.html.xpath(".//li/p/a[contains(@href, '.pdf')]/../.."):
            url = row.xpath(".//p/a/@href")[0]
            name = row.xpath(".//p/a/text()")[0]
            docket = name.split()[0]
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "url": url,
                    "date": str(self.year),
                }
            )

    def extract_from_text(self, scraped_text):
        pattern = re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4})")
        match = pattern.search(scraped_text)
        if match:
            date_filed = datetime.datetime.strptime(
                match.group(), "%B %d, %Y"
            ).strftime("%Y-%m-%d")
            metadata = {
                "OpinionCluster": {"date_filed": date_filed},
            }
            return metadata
