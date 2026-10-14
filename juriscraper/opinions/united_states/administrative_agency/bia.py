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

from httpx import Response
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import BackscrapeItem, SiteOptions, logger
from juriscraper.lib.auth_utils import get_justice_dot_gov_auth_cookies
from juriscraper.lib.exceptions import UnexpectedContentTypeError
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.lib.type_utils import (
    AsyncClientOptions,
    ExtractedMetadata,
    GetRequestOptions,
    PostRequestOptions,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[BackscrapeItem]):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[BackscrapeItem]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.justice.gov/eoir/ag-bia-decisions"
        self.volume = 0
        self.urls: list[HtmlElement] = []
        self.status = "Published"

    @override
    async def _process_html(self) -> None:
        if not self.test_mode_enabled():
            # Get last volume URL
            if not bool(self.urls):
                if not isinstance(self.html, HtmlElement):
                    raise ValueError(
                        "An HTML document must be downloaded before parsing."
                    )
                urls: list[HtmlElement] = self.html.xpath(
                    ".//table[1]/tbody/tr/td/a[contains(., 'Volume')]"
                )

                self.urls = sorted(
                    urls, key=HtmlElement.text_content, reverse=True
                )
            self.url = self.urls[self.volume].get("href")
            self.html = await super()._download()

        # Rows are sorted by date_filed descending on the source, but the
        # source only provides the year. We use date_filed_is_approximate
        # with the same year for every record, so without a tie-breaker CL
        # orders them by case name. If the first few names happen to already
        # exist, CL's DupChecker stops and never reaches newer opinions (#1934).
        # Assign a descending approximate date starting from the middle of the
        # year (one day apart per row) to preserve the source order and force
        # the dup check to see newer records first.
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//table")
        for index, row in enumerate(rows):
            summary = next(row.itersiblings("p"), None)
            summary = summary.text_content() if summary is not None else ""
            name: str = row.xpath(
                ".//td[1]//*[self::strong or self::b]/text()"
            )[0]

            if bool(row.xpath(".//td[1]/text()")):
                row_text: str = row.xpath(".//td[1]/text()")[-1]
            else:
                row_text: str = row.xpath(".//td[1]/p/text()")[-1]

            citation, year = row_text.split("(", 1)

            year_match = re.search(r"\d{4}", year)
            if year_match is None:
                raise ValueError(f"Could not parse opinion year: {year!r}")
            year = year_match.group(0)
            date = datetime(int(year), 7, 1) - timedelta(days=index)
            url: list[str] = row.xpath(".//td[2]//a/@href")
            docket = row.find(".//td[2]//a")
            docket = docket.text_content() if docket is not None else ""
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

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Can we extract the date filed from the text?

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        date = re.findall(
            r"Decided (?:(?:by (?:(?:Acting\s)?Attorney General|Board)|as amended)\s)?(.*\d{4})",
            scraped_text,
        )
        if not bool(date):
            logger.error("bia: unable to extract_from_text a date_filed")
            return {}

        date_filed = datetime.strptime(date[0], "%B %d, %Y").strftime(
            "%Y-%m-%d"
        )
        metadata: ExtractedMetadata = {
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
        *,
        doctor_options: AsyncClientOptions | None = None,
        doctor_request_options: PostRequestOptions | None = None,
        **kwargs: Unpack[GetRequestOptions],
    ) -> str | bytes:
        """Overrides regular download_content to handle the
        "I am not a robot challenge". See #1724
        """
        try:
            return await super().download_content(
                download_url,
                doctor_is_available,
                media_root,
                doctor_options=doctor_options,
                doctor_request_options=doctor_request_options,
                **kwargs,
            )
        except UnexpectedContentTypeError as exc:
            if exc.data is None:
                raise
            response = exc.data.get("response")
            if not isinstance(response, Response):
                raise
            # access HTML with JS variables to populate cookies
            html_text = response.text
            self.cookies = get_justice_dot_gov_auth_cookies(html_text)
            return await super().download_content(
                download_url,
                doctor_is_available,
                media_root,
                doctor_options=doctor_options,
                doctor_request_options=doctor_request_options,
                **kwargs,
            )
