"""Scraper for the California Attorney General
CourtID: calag
Court Short Name: California Attorney General
"""

import datetime

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[int | str]):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int | str]],
    ) -> None:
        cipher = "ECDHE-RSA-AES128-GCM-SHA256"
        kwargs.setdefault("verify", self.set_custom_adapter(cipher))
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.year = datetime.date.today().year
        self.url = f"https://oag.ca.gov/opinions/yearly-index?conclusion-year[value][year]={self.year}"
        self.back_scrape_iterable = list(range(1985, self.year + 1))
        self.status = "Published"

    def build_summaries(self, row: HtmlElement) -> str:
        """Build Summaries of opinions

        :param row: Row to collect from
        :return: Summary of the opinion
        """
        questions = row.findall("./td[2]")[0].text_content()
        conclusions = row.findall("./td[3]")[0].text_content()
        return f"QUESTIONS: {questions} CONCLUSIONS: {conclusions}"

    @override
    def _process_html(self) -> None:
        """Process California AG HTML

        :return: none
        """
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//table/tbody/tr[.//a]")
        for row in rows:
            docket: str = row.xpath(".//a//strong/text()")[0].strip()
            # Citation may not exist (yet?)
            citation: list[str] = row.xpath(".//strong/em/text()")
            self.cases.append(
                {
                    "url": row.xpath(".//a/@href")[0],
                    "citation": citation[0] if bool(citation) else "",
                    "docket": docket,
                    "date": row.xpath(".//td/span/text()")[0].strip(),
                    "name": f"California Attorney General Opinion {docket}",
                    "summary": self.build_summaries(row),
                }
            )

    @override
    async def _download_backwards(self, year: int | str) -> None:
        """Download backwards

        :param year: The year to scrape
        :return: None
        """
        self.url = f"https://oag.ca.gov/opinions/yearly-index?conclusion-year[value][year]={year}"
