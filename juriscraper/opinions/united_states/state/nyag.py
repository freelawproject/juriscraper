"""Scraper for the New York Attorney General
CourtID: nyag
Court Short Name: New York Attorney General
"""

import datetime

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
        self.year = datetime.date.today().year
        self.base_url = "https://ag.ny.gov/appeals-and-opinions/numerical-index?field_opinion_year_value=%d"
        self.url = self.base_url % self.year
        self.status = "Published"

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//div[@class='views-row']")
        for row in rows:
            metadata: list[str] = row.xpath(".//div/text()")
            docket, _, _, summary, *_ = metadata
            anchor: HtmlElement = row.xpath(".//div/span/p/a")[0]
            url = anchor.attrib["href"]
            case: str = row.xpath(".//div/span/p/a/text()")[0]
            self.cases.append(
                {
                    "name": case,
                    "docket": docket,
                    "url": url,
                    "summary": summary,
                    "date": f"{docket[:4]}-07-01",
                    "date_filed_is_approximate": True,
                }
            )
