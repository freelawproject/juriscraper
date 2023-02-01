"""
Scraper for Indiana Attorney General
CourtID: indianaag
Court Short Name: Indiana AG
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
        self.url = f"https://www.in.gov/attorneygeneral/about-the-office/advisory/official-opinions-of-the-indiana-attorney-general/"

    def _process_html(self):
        """Process the html

        :return: None
        """
        for row in self.html.xpath(".//p/a[contains(@href, '.pdf')]/.."):
            url = row.xpath(".//a/@href")[0]
            docket = row.text_content().split()[0]
            name = row.text_content().split(docket)[1]
            if "Click" in docket:
                continue
            if not self.test_mode_enabled():
                date = docket.split("-")[0]
            else:
                date = "2022-01-31"
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "url": url,
                    "date": date,
                }
            )

    def extract_from_text(self, scraped_text):
        """Extract date from pdf content

        :param scraped_text: The scraped text
        :return: Metadata containing date information for CL
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
