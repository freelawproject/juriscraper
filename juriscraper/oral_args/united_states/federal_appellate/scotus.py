"""Scraper for Supreme Court of U.S.
CourtID: scotus
Court Short Name: scotus
History:
 - 2014-07-20 - Created by Andrei Chelaru, reviewed by MLR
 - 2017-10-09 - Updated by MLR.
"""

from datetime import date, datetime

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite[int]):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "http://www.supremecourt.gov/oral_arguments/argument_audio.aspx"
        )
        self.back_scrape_iterable = list(range(2010, 2015))

    @override
    def _get_download_urls(self) -> list[str]:
        path = "id('list')//tr//a/text()"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        return list(map(self._return_download_url, self.html.xpath(path)))

    @staticmethod
    def _return_download_url(d: str) -> str:
        file_type = "mp3"  # or 'wma' is also available for any case.
        download_url = f"http://www.supremecourt.gov/media/audio/{file_type}files/{d}.{file_type}"
        return download_url

    @override
    def _get_case_names(self) -> list[str]:
        path = "id('list')//tr/td/span/text()"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        names: list[str] = self.html.xpath(path)
        return [s.lstrip(". ") for s in names]

    @override
    def _get_case_dates(self) -> list[date]:
        path = "id('list')//tr/td[2]//text()"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        dates: list[str] = self.html.xpath(path)
        return [
            datetime.strptime(s, "%m/%d/%y").date()
            for s in dates
            if "Date" not in s
        ]

    @override
    def _get_docket_numbers(self) -> list[str]:
        path = "id('list')//tr//a/text()"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(path)
        return texts

    @override
    async def _download_backwards(self, year: int) -> None:
        self.url = (
            f"http://www.supremecourt.gov/oral_arguments/argument_audio/{year}"
        )
        self.html = await self._download()
