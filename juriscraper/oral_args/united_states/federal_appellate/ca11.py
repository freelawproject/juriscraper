"""Scraper for Eleventh Circuit of Appeals
CourtID: ca11
Court Short Name: ca11
Author: Jon Andersen
Reviewer: mlr
Date created: 28 Aug 2018
"""

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear[int]):
    base_url = "https://www.ca11.uscourts.gov/oral-argument-recordings"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = self.base_url
        self.back_scrape_iterable = list(range(0, 52))

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//tr[not(th)]")
        for row in rows:
            # normalize docket numbers
            # get rid of "consolidated with" text
            # parse docket numbers like docketnum1 & docketnum2
            # also handle docketnum1\ndocketnum2\ndocketnum3
            # Return comma joined string like docketnum1, docketnum2
            docket: str = row.xpath("td[1]/text()")[0]
            docket = ", ".join(
                docket.strip()
                .upper()
                .replace("&", "\n")
                .replace(" AND ", "\n")
                .replace(",", "\n")
                .replace("CONS. WITH", "\n")
                .replace("CONSOLIDATED WITH", "\n")
                .split()
            )
            name: str = row.xpath("td[2]/text()")[0]
            date: str = row.xpath("td[3]/text()")[0]
            url: str = row.xpath("td[5]//@href")[0]
            self.cases.append(
                {"name": name, "url": url, "date": date, "docket": docket}
            )

    @override
    async def _download_backwards(self, i: int) -> None:
        self.url = f"{self.base_url}?page={i}"
        self.html = await self._download()
        self._process_html()
