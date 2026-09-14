"""Scraper for Dept of Justice Board of Immigration Appeals
CourtID: bia
Court Short Name: Dept of Justice Board of Immigration Appeals
Author: William Palin
Reviewer:
Type:
History:
    2021-12-18: Created by William E. Palin
    2024-05-07: Updated by grossir
    2025-04-25: Updated by quevon24
"""

import re
from datetime import datetime, timedelta
from typing import Any

from typing_extensions import override

from juriscraper.AbstractSite import logger
from juriscraper.lib.auth_utils import get_justice_dot_gov_auth_cookies
from juriscraper.lib.exceptions import UnexpectedContentTypeError
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # The source only gives the year, so every row shares an approximate date
    # and nothing places new rows first. #1934 #2152
    is_recency_ordered = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.justice.gov/eoir/ag-bia-decisions"
        self.volume = 0
        self.urls = None
        self.status = "Published"

    async def _process_html(self) -> None:
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
            self.html = await super()._download()

        # The source only gives the year. A descending approximate date, one
        # day apart per row, keeps the source order for consumers that don't
        # honour `is_recency_ordered` yet. #1934
        for index, row in enumerate(self.html.xpath("//table")):
            summary = row.xpath("string(following-sibling::p[1])")
            name = row.xpath(".//td[1]//*[self::strong or self::b]/text()")[0]

            if row.xpath(".//td[1]/text()"):
                row_text = row.xpath(".//td[1]/text()")[-1]
            else:
                row_text = row.xpath(".//td[1]/p/text()")[-1]

            citation, year = row_text.split("(", 1)

            year = re.search(r"\d{4}", year).group(0)
            date = datetime(int(year), 7, 1) - timedelta(days=index)
            url = row.xpath(".//td[2]//a/@href")
            docket = row.xpath("string(.//td[2]//a)")
            self.cases.append(
                {
                    "name": titlecase(name),
                    "citation": citation.strip(", "),
                    "url": url[0],
                    "docket": docket,
                    "date": date.strftime("%Y-%m-%d"),
                    "date_filed_is_approximate": True,
                    "summary": summary,
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict[str, Any]:
        """Can we extract the date filed from the text?

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        date = re.findall(
            r"Decided (?:(?:by (?:(?:Acting\s)?Attorney General|Board)|as amended)\s)?(.*\d{4})",
            scraped_text,
        )
        if not date:
            logger.error("bia: unable to extract_from_text a date_filed")
            return {}

        date_filed = datetime.strptime(date[0], "%B %d, %Y").strftime(
            "%Y-%m-%d"
        )
        metadata = {
            "OpinionCluster": {
                "date_filed": date_filed,
                "date_filed_is_approximate": False,
            },
        }
        return metadata

    @override
    async def download_content(
        self,
        download_url: str,
        doctor_is_available: bool = True,
        media_root: str = "",
    ) -> str | bytes:
        """Overrides regular download_content to handle the
        "I am not a robot challenge". See #1724
        """
        try:
            return await super().download_content(
                download_url, doctor_is_available, media_root
            )
        except UnexpectedContentTypeError as exc:
            # access HTML with JS variables to populate cookies
            html_text = exc.data["response"].text
            self.cookies = get_justice_dot_gov_auth_cookies(html_text)
            return await super().download_content(
                download_url, doctor_is_available, media_root
            )
