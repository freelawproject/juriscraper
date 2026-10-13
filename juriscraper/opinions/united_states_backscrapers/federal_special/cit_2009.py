import time
from datetime import date

from lxml import html
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states_backscrapers.federal_special import (
    cit_2010,
)


class Site(cit_2010.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "http://www.cit.uscourts.gov/SlipOpinions/SlipOps-2009.html"
        self.court_id = self.__module__

    @override
    def _get_case_dates(self) -> list[date]:
        case_dates = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            "//table[3]/tr/td[3][../td/a]"
        )
        for e in elements:
            date_string = html.tostring(
                e, method="text", encoding="unicode"
            ).strip()
            if date_string == "05/13/20009":
                # Special case.
                date_string = "05/13/2009"
            case_dates.append(
                date.fromtimestamp(
                    time.mktime(time.strptime(date_string, "%m/%d/%Y"))
                )
            )
        return case_dates

    @override
    def _get_nature_of_suit(self) -> None:
        return None
