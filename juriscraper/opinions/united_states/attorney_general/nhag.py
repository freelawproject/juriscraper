"""
Scraper for New Hampshire Attorney General
CourtID: nhag
Court Short Name: New Hampshire AG
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
        self.url = "https://www.doj.nh.gov/public-documents/opinions.htm"

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//a"):
            if (
                row.xpath(".//@href")
                and "/documents/" not in row.xpath(".//@href")[0]
            ):
                continue
            url = row.xpath(".//@href")
            if not url:
                continue

            docket = row.text_content()
            name = docket
            if self.test_mode_enabled():
                date = "2023-01-31"
            else:
                date = url[0].split("opinion-")[1][:4]
            self.cases.append(
                {
                    "url": url[0],
                    "docket": docket,
                    "name": name,
                    "date": date,
                    "date_filed_is_approximate": True,
                }
            )

    def extract_from_text(self, scraped_text):
        """Extract date from scrapted text

        :param scraped_text: the downloaded pdf
        :return: the metadata containing date information
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
