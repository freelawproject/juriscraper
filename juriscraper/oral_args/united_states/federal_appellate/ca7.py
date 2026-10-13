"""Scraper for Seventh Circuit of Appeals
CourtID: ca7
Court Short Name: ca7
Author: Andrei Chelaru
Reviewer: mlr
Date created: 19 July 2014
"""

from datetime import date, datetime

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "https://media.ca7.uscourts.gov/oralArguments/oar.jsp?caseyear=&casenumber=&period=Past+month"

    @override
    def _get_download_urls(self) -> list[str]:
        path = "//tr[@bgcolor]/td[5]//@href"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(path)
        return texts

    @override
    def _get_case_names(self) -> list[str]:
        path = "//tr[@bgcolor]/td[2]/text()"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(path)
        return texts

    @override
    def _get_case_dates(self) -> list[date]:
        path = "//tr[@bgcolor]/td[4]/text()"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        return list(map(self._return_case_date, self.html.xpath(path)))

    @staticmethod
    def _return_case_date(s: str) -> date:
        return datetime.strptime(s.strip(), "%m/%d/%Y").date()

    @override
    def _get_docket_numbers(self) -> list[str]:
        path = "//tr[@bgcolor]/td[1]/text()"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(path)
        return texts
