"""Scraper for Supreme Court of Virgin Islands
CourtID: virginislands
Court Short Name: Virgin Islands
Author: William Edward Palin
History:
  2023-01-21: Created by William Palin
"""

import urllib.parse
from datetime import date, datetime, timedelta

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, convert_date_string
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
        self.url = (
            "https://supreme.vicourts.org/court_opinions/published_opinions"
        )
        self.status = "Published"
        today = date.today()
        self.previous_date = today - timedelta(days=60)
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        if self.test_mode_enabled():
            self.previous_date = datetime(2023, 9, 21).date()

        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(".//tr/td/..")
        for s in elements:
            cells = s.findall(".//td")
            if not bool(cells[0].text_content()):
                continue

            judges = cells[3].text_content()
            name = cells[0].text_content()
            date = cells[1].text_content().replace("/", "-")
            date_object = convert_date_string(date)
            if date_object is None:
                raise ValueError("An opinion date is required")
            docket = cells[2].text_content()
            citation = cells[4].text_content()
            if date_object < self.previous_date:
                continue
            u: str = s.xpath(".//td/a/@href")[0]
            url = urllib.parse.quote(u, safe="/:")
            self.cases.append(
                {
                    "name": name,
                    "date": date,
                    "docket": docket,
                    "citation": citation,
                    "judge": judges,
                    "url": url,
                }
            )
