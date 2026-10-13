"""This site is pretty bad. Very little HTML; everything is separated by
<br> tags. There is currently a case at the bottom of the page from 2009
that has incomplete meta data. You can see it in the example document.
"""

from datetime import date

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "http://www2.ca3.uscourts.gov/recentop/week/recprec.htm"
        self.court_id = self.__module__

    @override
    def _get_case_names(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            '//a[contains(@href, "opinarch")]/text()'
        )
        return texts

    @override
    def _get_download_urls(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            '//a[contains(@href, "opinarch")]/@href'
        )
        return texts

    @override
    def _get_case_dates(self) -> list[date | None]:
        dates = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        text_strings: list[str] = self.html.xpath("//text()")
        for text_string in text_strings:
            if not text_string.lower().startswith("filed"):
                continue
            else:
                date_string = text_string.split(" ")[1]
                date_string = date_string.strip().strip(",")
                dates.append(convert_date_string(date_string))
        return dates

    @override
    def _get_docket_numbers(self) -> list[str]:
        docket_numbers = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        text_strings: list[str] = self.html.xpath("//text()")
        for text_string in text_strings:
            if not text_string.lower().startswith("filed"):
                continue
            else:
                docket_numbers.append(text_string.split(" ")[3])
        return docket_numbers

    @override
    def _get_precedential_statuses(self) -> list[str]:
        statuses = []
        for _ in range(0, len(self)):
            if "recprec" in (self.url if self.url is not None else ""):
                statuses.append("Published")
            elif "recnonprec" in (self.url if self.url is not None else ""):
                statuses.append("Unpublished")
            else:
                statuses.append("Unknown")
        return statuses

    @override
    def _get_lower_courts(self) -> list[str]:
        lower_courts = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            '//a[contains(@href, "opinarch")]'
        )
        for e in elements:
            text_strings: list[str] = e.xpath("./following-sibling::text()[1]")
            text_string = " ".join(text_strings)
            if (
                text_string.lower().startswith("filed")
                or text_string.strip() == ""
            ):
                lower_courts.append("Unknown")
            else:
                lower_courts.append(text_string.strip())
        return lower_courts
