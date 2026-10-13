"""Scraper for Dept of Justice Office of Legal Counsel
CourtID: bia
Court Short Name: Dept of Justice OLC
Author: William Palin
Reviewer:
Type:
History:
    2022-01-14: Created by William E. Palin
"""

from datetime import date, datetime
from urllib.parse import urlencode

from httpx import Response
from lxml.html import HtmlElement
from pydantic import InstanceOf, TypeAdapter
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.auth_utils import get_justice_dot_gov_auth_cookies
from juriscraper.lib.exceptions import UnexpectedContentTypeError
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import (
    AsyncClientOptions,
    GetRequestOptions,
    PostRequestOptions,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

_backfill_adapter = TypeAdapter(tuple[InstanceOf[date], InstanceOf[date]])


class Site(OpinionSiteLinear[tuple[date, date] | int]):
    base_url = "https://www.justice.gov/olc/opinions"
    days_interval = 180
    first_opinion_date = datetime(1934, 3, 16)

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date] | int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = self.base_url
        self.status = "Published"
        self.url = f"{self.base_url}?items_per_page=40"
        self.make_backscrape_iterable(kwargs)
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        for row in self.html.findall(".//article"):
            name = row.findall(".//h2")[0].text_content().strip()
            if not bool(name):
                continue
            url: str = row.xpath(".//a/@href")[0]
            date_filed = row.findall(".//time")[0].text_content()
            summary = row.findall(".//p")[0].text_content()
            self.cases.append(
                {
                    "date": date_filed,
                    "name": name,
                    "url": url,
                    "summary": summary,
                    "docket": "",  # Docket numbers don't appear to exist.
                }
            )

    @override
    async def _download_backwards(
        self, dates: tuple[date, date] | int
    ) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        dates = _backfill_adapter.validate_python(dates, strict=True)
        logger.info("Backscraping for range %s %s", *dates)
        params = {
            "search_api_fulltext": "",
            "start_date": dates[0].strftime("%m/%d/%Y"),
            "end_date": dates[1].strftime("%m/%d/%Y"),
            "sort_by": "field_date",
            "items_per_page": "40",
        }
        self.url = f"{self.base_url}?{urlencode(params)}"
        self.html = await self._download()
        self._process_html()

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
