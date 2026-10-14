"""Scraper for Missouri
CourtID: mo
Court Short Name: MO
Author: Ben Cassedy
Date created: 04/27/2014
"""

from datetime import date

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
        self.court = "Supreme"
        self.url = self.build_url()
        self.status = "Published"

    def build_url(self) -> str:
        year = date.today().year
        return f"https://www.courts.mo.gov/page.jsp?id=12086&dist=Opinions%20{self.court}&date=all&year={year}#all"

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(
            "//div[@class='margin-bottom-15']"
        )
        for row in rows:
            date = row.findall(".//input")[0].attrib["value"]
            for opinion in row.findall(
                ".//div[@class='list-group-item-text']"
            ):
                links = opinion.findall("a")
                if len(links) != 2:
                    continue
                url = opinion.findall("a")[1].attrib["href"]
                all_text: list[str] = opinion.xpath(".//text()")
                case_metadata = [
                    t.strip() for t in all_text if bool(t.strip())
                ]
                docket, _, name, _, author, _, vote = case_metadata
                self.cases.append(
                    {
                        "name": name,
                        "docket": docket[:-1],
                        "url": url,
                        "date": date,
                        "disposition": vote.split(".")[0].strip(),
                        "author": author,
                        "judge": vote.split(".", 1)[1].strip(),
                    }
                )
