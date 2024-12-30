"""Scraper for Dept of Justice Board of Immigration Appeals
CourtID: bia
Court Short Name: Dept of Justice Board of Immigration Appeals
Author: William Palin
Reviewer:
Type:
History:
    2021-12-18: Created by William E. Palin
    2024-05-07: Updated by grossir
"""

import re
from datetime import datetime
from typing import Any, Dict

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.justice.gov/eoir/ag-bia-decisions"
        self.volume = 0
        self.urls = None
        self.status = "Published"

    def _process_html(self) -> None:
        if not self.test_mode_enabled():
            # Get last volume URL
            if not self.urls:
                urls = self.html.xpath(
                    ".//table[1]/tbody/tr/td/a[contains(., 'Volume')]"
                )

                def get_text(elem):
                    return elem.text_content()

                self.urls = sorted(urls, key=get_text, reverse=True)
            self.url = self.urls[self.volume].get("href")
            self.html = super()._download()

        for row in self.html.xpath("//table"):
            summary = row.xpath("string(following-sibling::p[1])")
            name = row.xpath(".//td[1]/*[self::strong or self::b]/text()")[0]
            row_text = row.xpath(".//td[1]/text()")[-1]
            citation, year = row_text.split("(", 1)

            year = re.search(r"\d{4}", year).group(0)
            url = row.xpath(".//td[2]/a/@href")
            docket = row.xpath("string(.//td[2]/a)")
            self.cases.append(
                {
                    "name": name,
                    "citation": citation.strip(", "),
                    "url": url[0],
                    "docket": docket,
                    "date": f"{year}-07-01",
                    "date_filed_is_approximate": True,
                    "summary": summary,
                }
            )

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Can we extract the date filed from the text?

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        date = re.findall(
            r"Decided (by (Acting\s)?Attorney General )?(.*\d{4})",
            scraped_text,
        )[0][-1]
        date_filed = datetime.strptime(date, "%B %d, %Y").strftime("%Y-%m-%d")
        metadata = {
            "OpinionCluster": {
                "date_filed": date_filed,
                "date_filed_is_approximate": False,
            },
        }
        return metadata
