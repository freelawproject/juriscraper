# Scraper for the United States Court of International Trade
# CourtID: cit
# Court Short Name: Ct. Int'l Trade
# Neutral Citation Format: Ct. Int'l Trade No. 12-1
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
        # This is a special backscraper to deal with problems on the 2008 page.
        self.url = "http://www.cit.uscourts.gov/SlipOpinions/SlipOps-2008.html"
        self.court_id = self.__module__

    @override
    def _get_download_urls(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            "//table[3]/tr[position() > 1]/td[1]/a/@href | //table[3]/tr[position() > 1]/td[1]/font/a/@href"
        )
        return texts

    @override
    def _get_citations(self) -> list[str]:
        neutral_citations = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            "//table[3]/tr[position() > 1]/td[1]"
        )
        for e in elements:
            s = html.tostring(e, method="text", encoding="unicode").strip()
            neutral_citations.append(s)
        return neutral_citations

    @override
    def _get_case_names(self) -> list[str]:
        case_names = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            "//table[3]/tr[position() > 1]/td[2]"
        )
        for e in elements:
            t = html.tostring(e, method="text", encoding="unicode")
            # We strip "Errata: mm/dd/yyyy" from the case names of errata docs.
            if "Errata" in t:
                case_names.append(t.strip()[:-18])
            # We strip "Public version posted on mm/dd/yyyy" from some case names.
            elif "posted on" in t:
                case_names.append(t.strip()[:-34])
            else:
                case_names.append(t.strip())
        return case_names

    @override
    def _get_precedential_statuses(self) -> list[str]:
        statuses = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            "//table[3]/tr[position() > 1]/td[2]"
        )
        for e in elements:
            s = (
                html.tostring(e, method="text", encoding="unicode")
                .lower()
                .strip()
            )
            if "errata" in s:
                statuses.append("Errata")
            else:
                statuses.append("Published")
        return statuses

    # This does not capture the release dates for the errata documents.
    # The errata release date is listed in column 2. This will use the original
    # release date instead.
    @override
    def _get_case_dates(self) -> list[date]:
        case_dates = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            "//table[3]/tr[position() > 1]/td[3]"
        )
        for e in elements:
            if (
                html.tostring(e, method="text", encoding="unicode").strip()
                == "08/05/20008"
            ):
                date_string = "08/05/2008"
                case_dates.append(
                    date.fromtimestamp(
                        time.mktime(time.strptime(date_string, "%m/%d/%Y"))
                    )
                )
            else:
                date_string = html.tostring(
                    e, method="text", encoding="unicode"
                ).strip()
                case_dates.append(
                    date.fromtimestamp(
                        time.mktime(time.strptime(date_string, "%m/%d/%Y"))
                    )
                )
        return case_dates

    # Because there can be multiple docket numbers we have to replace some newlines.
    @override
    def _get_docket_numbers(self) -> list[str]:
        docket_numbers = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            "//table[3]/tr[position() > 1]/td[4]"
        )
        for e in elements:
            s = html.tostring(e, method="text", encoding="unicode").strip()
            docket_numbers.append(s.replace("\r\n", " &"))
        return docket_numbers

    # Comment out the following section if backscraping years 1999-2005.
    # Because there are sometimes multiple judges we have to strip some whitespace.
    @override
    def _get_judges(self) -> list[str]:
        judges = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            "//table[3]/tr[position() > 1]/td[5]"
        )
        for e in elements:
            s = html.tostring(e, method="text", encoding="unicode")
            judges.append(s.strip())
        return judges
