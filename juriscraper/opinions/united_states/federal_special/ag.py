"""Scraper for the United States Department of Justice Attorney General
CourtID: ag
Court Short Name: United States Attorney General
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
        self.url = "https://www.justice.gov/olc/opinions?items_per_page=40"
        self.status = "Published"
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        for row in self.html.findall(".//article"):
            name = row.findall(".//h2")[0].text_content().strip()
            url: str = row.xpath(".//a/@href")[0]
            date = row.findall(".//time")[0].text_content()
            if not bool(name):
                continue
            summary = row.findall(".//p")[0].text_content()
            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "url": url,
                    "summary": summary,
                    "docket": "",  # Docket numbers don't appear to exist.
                }
            )
