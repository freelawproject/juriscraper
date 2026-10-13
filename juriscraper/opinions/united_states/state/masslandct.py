"""
Scraper for Massachusetts Land Court
CourtID: massland
Court Short Name: Mass Land Ct
Author: William Palin
Court Contact:
Reviewer:
History:
 - 2020-12-05: Created.
Notes:
 - On Masscases.com they list all the cases on one long page.  A very atypical pattern
"""

import datetime

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import (
    CaseNameTweaker,
    convert_date_string,
    titlecase,
)
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "http://www.masscases.com/land_date.html"
        self.court_id = self.__module__
        self.year: str | None = None
        self.expected_content_types = ["text/html"]
        self.should_have_results = True

    @override
    def _get_download_urls(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        links: list[HtmlElement] = self.html.xpath(
            f'//*[@id="{self.year}"]/../following-sibling::section/table//tr/td[2]/a'
        )
        return [row.attrib["href"] for row in links]

    @override
    def _get_docket_numbers(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        links: list[HtmlElement] = self.html.xpath(
            f'//*[@id="{self.year}"]/../following-sibling::section/table//tr/td[2]/a'
        )
        return [row.text_content() for row in links]

    @override
    def _get_case_names(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        names: list[str] = self.html.xpath(
            f'//*[@id="{self.year}"]/../following-sibling::section/table//tr/td[3]/text()'
        )
        return [titlecase(case_name) for case_name in names]

    @override
    def _get_case_dates(self) -> list[datetime.date | None]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        self.year = self.html.xpath('//li[@class="menuitems"]/a/text()')[-1]
        dates: list[str] = self.html.xpath(
            f'//*[@id="{self.year}"]/../following-sibling::section/table//tr/td[1]/text()'
        )
        return [
            convert_date_string(
                date_text.replace("AUGUSET", "August").replace(
                    "OCOTBER", "October"
                ),
                fuzzy=True,
            )
            for date_text in dates
        ]

    @override
    def _get_precedential_statuses(self) -> list[str]:
        return len(self) * ["Published"]
