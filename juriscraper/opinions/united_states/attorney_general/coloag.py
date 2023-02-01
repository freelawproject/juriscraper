"""
Scraper for Colorado AG
CourtID: coloag
Court Short Name: Colorado AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
import datetime
import re

from lxml.html import tostring

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://coag.gov/attorney-general-opinions/"

    def _process_html(self):
        """Process the html

        :return: None
        """
        if not self.test_mode_enabled():
            m = re.findall(
                r"\d+ Formal AG Opinions", tostring(self.html).decode()
            )
            if not m:
                return
            year = m[0].split()[0]
            key = m[0].replace(" ", "-")
            self.url = f"https://coag.gov/attorney-general-opinions/{key}/"
            self.html = super()._download()
        else:
            year = "2021-01-31"
        for row in self.html.xpath(".//li/a[contains(@href, '.pdf')]/.."):
            url = row.xpath(".//a/@href")[0].replace("http", "https")
            name = row.xpath(".//a/text()")[0]
            self.cases.append(
                {
                    "url": url,
                    "name": name,
                    "docket": name,
                    "summary": row.text_content(),
                    "date": year,
                    "date_filed_is_approximate": True,
                }
            )

    def extract_from_text(self, scraped_text):
        """Extract date info from text

        :param scraped_text: Scraped text
        :return: The metadata containing date filed
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
