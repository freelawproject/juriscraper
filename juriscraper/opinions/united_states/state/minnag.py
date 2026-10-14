"""Scraper for Minnesota Attorney General Opinions
CourtID: minnag
Court Short Name: MN
Author: David Cook
Reviewer:
"""

import re
from datetime import date

from lxml.html import HtmlElement
from typing_extensions import override

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ag.state.mn.us/office/opinions/DATE.asp"
        self.opinions = []
        self.should_have_results = True

    @override
    async def _download(self, request_dict=None) -> HtmlElement:
        if request_dict is None:
            request_dict = {}
        html = await super()._download(request_dict)
        self._extract_case_data_from_html(html)
        return html

    def _extract_case_data_from_html(self, html: HtmlElement) -> None:
        for p in html.xpath("//div[@id='content']/div[@id='op']/p"):
            text: str = p.xpath("a/strong/following-sibling::text()[1]")[0]
            name = " ".join(
                text.split()[1:]
            )  # strip leading dash charater, which can be one of various unicode dash characters
            name = re.sub("\\s+", " ", name).strip()
            summary: str = " ".join(
                p.xpath(
                    "br/following-sibling::text() | br/following-sibling::*//text()"
                )
            )
            summary = re.sub("\\s+", " ", summary).strip()

            self.opinions.append(
                {
                    "name": name,
                    "url": p.xpath("a/@href")[0],
                    "date": convert_date_string(p.xpath("a/strong/text()")[0]),
                    "summary": summary,
                }
            )

    @override
    def _get_case_names(self) -> list[str]:
        return [opinion["name"] for opinion in self.opinions]

    @override
    def _get_download_urls(self) -> list[str]:
        return [opinion["url"] for opinion in self.opinions]

    @override
    def _get_case_dates(self) -> list[date | None]:
        return [opinion["date"] for opinion in self.opinions]

    @override
    def _get_summaries(self) -> list[str]:
        return [opinion["summary"] for opinion in self.opinions]

    @override
    def _get_precedential_statuses(self) -> list[str]:
        return ["Published"] * len(self.opinions)
