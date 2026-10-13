"""Scraper for the United States Court of Appeals for the Armed Forces
CourtID: armfor
Court Short Name: C.A.A.F."""

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[str]):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[str]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = [""]
        self.url = (
            "https://www.armfor.uscourts.gov/newcaaf/opinions/CurrentOpins.htm"
        )
        self.row_base_path = (
            ".//td/font/a[contains(@href, '.pdf')]/ancestor::tr"
        )
        self.status = "Published"

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(self.row_base_path)
        for row in rows:
            case_name, docket, date, cite = row.findall(".//td")
            cite = "" if "xx" in cite.text_content() else cite.text_content()
            self.cases.append(
                {
                    "name": case_name.text_content(),
                    "url": docket.xpath(".//a/@href")[0],
                    "date": date.text_content().strip(),
                    "citation": cite,
                    "docket": docket.text_content().split()[0],
                }
            )
