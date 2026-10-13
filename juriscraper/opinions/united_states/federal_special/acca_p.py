"""Scraper for Army Court of Criminal Appeals
CourtID: acca
Reviewer: None
History:
  2015-01-08: Created by mlr
  2016-03-17: Website appears to be dead. Scraper disabled in __init__.py.
  2019-09-11: Rewritten by arderyp to user Linear pattern
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
        self.url = "https://www.jagcnet.army.mil/ACCALibrary/cases/opinions/OC"
        self.status = "Published"
        self.expected_content_types = ["application/octet-stream"]
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(
            '//*[@id="Opinions_ResizeContainer"]/table/tbody/tr'
        )
        for row in rows:
            col1, col2, col3 = row.findall(".//td")
            url: list[str] = col1.xpath(".//a/@href")
            if not bool(url):
                continue
            name = col1.text_content()
            docket = col2.text_content()
            date = col3.text_content()
            self.cases.append(
                {
                    "date": date.strip(),
                    "docket": docket.strip(),
                    "name": name.strip(),
                    "url": url[0],
                }
            )
