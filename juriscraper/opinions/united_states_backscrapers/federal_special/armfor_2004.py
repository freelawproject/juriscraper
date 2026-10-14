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
        self.url = (
            "http://www.armfor.uscourts.gov/newcaaf/opinions/2004Term.htm"
        )
        self.court_id = self.__module__

    @override
    def _get_case_names(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath("//table//tr/td[1]/font/text()")
        return texts

    @override
    def _get_download_urls(self) -> list[str]:
        download_urls = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            "//table//table//tr[position() > 1]/td[2]/div/font/a[2]/@href"
        )
        for t in texts:
            download_urls.append(t)
        return download_urls

    @override
    def _get_case_dates(self) -> list[date]:
        dates = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            "//table/tr[3]/td[2]/blockquote/table/tbody/tr[position() > 1]/td[3]"
        )
        for e in elements:
            s = html.tostring(e, method="text", encoding="unicode")
            s = s.replace("June", "Jun").replace("July", "Jul")
            s = " ".join(s.split())
            dates.append(
                date.fromtimestamp(time.mktime(time.strptime(s, "%b %d, %Y")))
            )
        return dates

    @override
    def _get_docket_numbers(self) -> list[str]:
        docket_numbers = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            "//table/tr[3]/td[2]/blockquote/table/tbody/tr/td[2]/div/font/a[1]/text()"
        )
        for t in texts:
            docket_numbers.append(t)
        return docket_numbers

    @override
    def _get_precedential_statuses(self) -> list[str]:
        return ["Published"] * len(self)

    @override
    def _get_citations(self) -> list[str]:
        neutral_citations = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            "//table/tr[3]/td[2]/blockquote/table/tbody/tr[position() > 1]/td[4]"
        )
        for e in elements:
            s = html.tostring(e, method="text", encoding="unicode")
            neutral_citations.append(s)
        return neutral_citations
