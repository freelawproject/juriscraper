import time
from datetime import date

from lxml import html
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.federal_special import cit


class Site(cit.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "http://www.cit.uscourts.gov/SlipOpinions/SlipOps-2012.html"
        self.court_id = self.__module__

    @override
    def _get_download_urls(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath("//table[4]//tr/td[1]//a/@href")
        return texts

    @override
    def _get_citations(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath("//table[4]//tr/td[1]//a/text()")
        return texts

    @override
    def _get_case_names(self) -> list[str]:
        # Exclude confidential rows by ensuring there is a sibling row that
        # contains an anchor (which confidential cases do not)
        # There is also one stray case within a <p> tag we have to catch.
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            "//table[4]//tr[position() > 1]/td[2][../td//a]/text()[1] | //table[4]//tr[position() > 1]/td[2][../td//a]/p/text()[1]"
        )
        return texts

    @override
    def _get_precedential_statuses(self) -> list[str]:
        return ["Published"] * len(self)

    @override
    def _get_case_dates(self) -> list[date]:
        # This does not capture the release dates for the errata documents.
        # The errata release date is listed in column 2. This will use the
        # original release date instead.
        dates: list[date] = []
        date_formats = ["%m/%d/%Y", "%m/%d/%y"]
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        date_strings: list[str] = self.html.xpath(
            "//table[4]//tr/td[3][../td//a]/text()"
        )
        for date_string in date_strings:
            for date_format in date_formats:
                try:
                    d = date.fromtimestamp(
                        time.mktime(time.strptime(date_string, date_format))
                    )
                    dates.append(d)
                    break
                except ValueError:
                    # Try the next format
                    continue
        return dates

    @override
    def _get_docket_numbers(self) -> list[str]:
        docket_numbers = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            "//table[4]//tr[position() > 1]/td[4][../td//a]"
        )
        for e in elements:
            docket_numbers.append(
                html.tostring(e, method="text", encoding="unicode").strip()
            )
        return docket_numbers

    @override
    def _get_judges(self) -> list[str]:
        judges = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            "//table[4]//tr[position() > 1]/td[5][../td//a]"
        )
        for e in elements:
            s = html.tostring(e, method="text", encoding="unicode")
            judges.append(s)
        return judges

    @override
    def _get_nature_of_suit(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            "//table[4]//tr/td[6][../td//a]/text()"
        )
        return texts
