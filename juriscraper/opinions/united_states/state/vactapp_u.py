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
        self.url = "https://www.vacourts.gov/wpcau.htm"
        self.status = "Unpublished"
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//p")
        for row in rows:
            links = row.findall(".//a")
            name: list[str] = row.xpath(".//b/text()")
            if not bool(name):
                continue
            date, disposition, *_ = row.text_content().splitlines()
            date = date.split(name[0])[1]
            self.cases.append(
                {
                    "name": name[0].strip(),
                    "docket": links[0].attrib["href"].split("/")[-1][:-4],
                    "url": links[0].attrib["href"],
                    "disposition": disposition,
                    "date": date.strip(),
                }
            )
