"""Scraper for the Texas Attorney General
CourtID: texag
Court Short Name: Texas Attorney General
History:
    2017-02-04: Created by Ardery
    2018-10-13: Retired by Ardery
    2023-01-28: Updated by William E. Palin
"""

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "https://texasattorneygeneral.gov/opinions"
        self.expected_content_types = ["application/pdf"]
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        cases: list[HtmlElement] = self.html.xpath(
            "//div[@class='sidebar-ag-opinion-content']"
        )
        for case in cases:
            docket = case.findall(".//h4")[0].text_content().strip()
            summary = case.findall(".//p")[0].text_content().strip()
            url: str = case.xpath(".//a[contains(@href, '.pdf')]/@href")[0]
            name = f"Untitled Texas Attorney General Opinion: {docket}"
            date: str = case.xpath(
                ".//div[@class='sidebar-ag-opinion-casedate']/text()"
            )[0].strip()
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "date": date,
                    "url": url,
                    "summary": summary,
                    "status": "Published",
                }
            )
