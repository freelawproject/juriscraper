"""
Scraper for Massachusetts Appeals Court Rule 23.0 (formerly Rule 1:28)
CourtID: massappct
Court Short Name: Mass App Ct
Author: William Palin
Court Contact: SJCReporter@sjc.state.ma.us (617) 557-1030
Reviewer:
Date: 2020-02-27
"""

from datetime import date, timedelta
from urllib.parse import urlencode

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.case_date = date.today()
        self.backwards_days = 14
        self.base = "https://128archive.com"
        self.url = self.make_url()
        self.court_id = self.__module__
        self.expected_content_types = ["text"]

    def make_url(self) -> str:
        """Build the urls to query

        :return: The url parameters (encoded)
        """
        start_date = self.case_date - timedelta(days=self.backwards_days)
        first_date = start_date.strftime("%m/%d/%Y")
        end_date = self.case_date.strftime("%m/%d/%Y")
        self.parameters = (
            ("Action", "search"),
            ("DocketNumber", ""),
            ("PartyName", ""),
            ("ReleaseDateFrom", first_date),
            ("ReleaseDateTo", end_date),
            ("Keywords", ""),
            (
                "SortColumnName",
                [
                    "Release Date Descending Order",
                    "Release Date Descending Order",
                ],
            ),
            ("SortOrder", ""),
            ("CurrentPageNo", "1"),
            ("Pages", "1"),
            ("PageSize", "100"),
        )
        return f"{self.base}/?{urlencode(self.parameters)}"

    @override
    def _process_html(self) -> None:
        """Process the data

        :return: None
        """
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//div[@data-rowtype]")
        for row in rows:
            metadata: list[str] = row.xpath(
                ".//div[@class='col-md-7 font-bold']/text()"
            )
            docket, name, date = metadata
            path: str = row.xpath(".//div/div/a/@href")[0]
            self.cases.append(
                {
                    "date": date.strip(),
                    "docket": docket.strip(),
                    "name": titlecase(name.strip()),
                    "url": path,
                    "status": "Unpublished",
                }
            )
