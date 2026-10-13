"""
Scraper for Indiana Supreme Court archive before 6/6/2005
CourtID: ind
Court Short Name: Ind.
Auth: Mike Lissner <mike@freelawproject.org>
Reviewer:
History:
    2014-09-03: Renamed to ind_2005.py by janderse
"""

import time
from datetime import date

from lxml import html
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "http://www.in.gov/judiciary/opinions/previous/archsup.html"
        self.court_id = self.__module__

    @override
    def _get_case_names(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath("//table/tr/td[1]/font/a/text()")
        return texts

    @override
    def _get_case_dates(self) -> list[date]:
        dates = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        link_strings: list[str] = self.html.xpath(
            "//table/tr/td[4]/font/a/@href"
        )
        for link_string in link_strings:
            date_string = link_string.split("/")[-1].split(".")[0][:-2]
            if date_string == "12319701-fs":
                # special case (there's always *one*)
                dates.append(
                    date.fromtimestamp(
                        time.mktime(time.strptime("123197", "%m%d%y"))
                    )
                )
            elif len(date_string) == 4:
                dates.append(
                    date.fromtimestamp(
                        time.mktime(
                            time.strptime(f"{date_string}98", "%m%d%y")
                        )
                    )
                )
            elif len(date_string) == 5:
                dates.append(
                    date.fromtimestamp(
                        time.mktime(time.strptime(f"0{date_string}", "%m%d%y"))
                    )
                )
            elif len(date_string) == 6:
                dates.append(
                    date.fromtimestamp(
                        time.mktime(time.strptime(date_string, "%m%d%y"))
                    )
                )
            else:
                print(date_string)
        return dates

    @override
    def _get_download_urls(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath("//table/tr/td[4]/font/a/@href")
        return texts

    @override
    def _get_docket_numbers(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        cells: list[HtmlElement] = self.html.xpath("//table/tr/td[2]")
        return [
            html.tostring(e, method="text", encoding="unicode") for e in cells
        ]

    @override
    def _get_precedential_statuses(self) -> list[str]:
        return ["Published"] * len(self)
