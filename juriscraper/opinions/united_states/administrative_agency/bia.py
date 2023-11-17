"""Scraper for Dept of Justice Board of Immigration Appeals
CourtID: bia
Court Short Name: Dept of Justice Board of Immigration Appeals
Author: William Palin
Reviewer:
Type:
History:
    2021-12-18: Created by William E. Palin
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

    def _process_html(self):
        if not self.test_mode_enabled():
            if not self.urls:
                urls = self.html.xpath(
                    ".//table[1]/tbody/tr/td/a[contains(., 'Volume')]"
                )

                def get_text(elem):
                    return elem.text_content()

                self.urls = sorted(urls, key=get_text, reverse=True)
            self.url = self.urls[self.volume].get("href")
            self.html = super()._download()
        table = self.html.xpath(".//table")[0]
        for row in table.xpath(".//strong"):
            name = row.text_content().strip().strip(",")
            row_text = row.xpath("..")[0].text_content()
            if "BIA" not in row_text:
                continue
            if not name:
                continue
            citation, year = row_text.split(name)[1].split("(")
            cells = row.xpath("..")[0].xpath(
                "following-sibling::td[position() <= 2]"
            )
            if not cells:
                continue
            url = cells[0].xpath(".//a/@href")
            docket = cells[0].xpath(".//a")[0].text_content()
            if not url:
                continue
            self.cases.append(
                {
                    "name": name,
                    "citation": citation,
                    "url": url[0],
                    "docket": docket,
                    "date": f"{year.split()[1]}-07-01",
                    "date_filed_is_approximate": True,
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
