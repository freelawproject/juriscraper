"""
Backscraper for Indiana Supreme Court
CourtID: ind
Court Short Name: Ind.
Auth: Mike Lissner <mike@freelawproject.org>
Reviewer:
History:
    2014-09-02: Bug fix by Jon Andersen - recognize "(NFP)" in case name
    2014-09-03: Moved to backscrapers
"""

import time
from datetime import date

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import BackscrapeItem, SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite[BackscrapeItem]):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[BackscrapeItem]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "http://www.in.gov/judiciary/opinions/archsup.html"
        self.court_id = self.__module__
        self.my_precedential_statuses = []

    @override
    def _get_case_names(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        raw_case_names: list[str] = self.html.xpath(
            "//table/tr/td[3]/table/tr[4]//table/tr[position() > 1]/td[2]//a/text()"
        )
        case_names = []
        self.my_precedential_statuses = []
        for case_name in raw_case_names:
            if case_name.find("(NFP)") >= 0:
                case_names.append(case_name.replace("(NFP)", "").strip())
                self.my_precedential_statuses.append("Unpublished")
            else:
                case_names.append(case_name)
                self.my_precedential_statuses.append("Published")
        return case_names

    @override
    def _get_download_urls(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            "//table/tr/td[3]/table/tr[4]//table/tr[position() > 1]/td[2]//a/@href"
        )
        return texts

    @override
    def _get_case_dates(self) -> list[date | str]:
        dates: list[date | str] = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        date_strings: list[str] = self.html.xpath(
            "//table/tr/td[3]/table/tr[4]//table/tr[position() > 1]/td[1]//font/text()"
        )
        for date_string in date_strings:
            val = date_string.strip()
            if val == "":
                dates.append("")
            else:
                dates.append(
                    date.fromtimestamp(
                        time.mktime(time.strptime(val, "%m/%d/%y"))
                    )
                )
        return dates

    @override
    def _get_docket_numbers(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            "//table/tr/td[3]/table/tr[4]//table/tr[position() > 1]/td[4]//font/text()"
        )
        return texts

    @override
    def _get_lower_court_numbers(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        numbers: list[str] = self.html.xpath(
            "//table/tr/td[3]/table/tr[4]//table/tr[position() > 1]/td[3]//font/text()"
        )
        return [e if e.strip() != "N/A" else "" for e in numbers]

    @override
    def _get_precedential_statuses(self) -> list[str]:
        return self.my_precedential_statuses
