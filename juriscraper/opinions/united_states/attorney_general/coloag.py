"""
Scraper for Colorado AG
CourtID: coloag
Court Short Name: Colorado AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
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
            year = "2021"
        for row in self.html.xpath(".//li/a[contains(@href, '.pdf')]/.."):
            url = row.xpath(".//a/@href")[0]
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
