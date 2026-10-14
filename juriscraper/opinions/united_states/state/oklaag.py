# Scraper for Oklahoma Attorney General Opinions
# CourtID: oklaag
# Court Short Name: OK
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05

from datetime import datetime

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import okla


class Site(okla.Site):
    # Inherit cleanup_content from Okla
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        year = datetime.today().year
        self.url = f"https://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKAG&year={year}&level=1"
        self.status = "Published"
        self.expected_content_types = ["text/html"]

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(
            "//div/p['@class=document']"
        )[::-1]
        for row in rows:
            if "OK" not in row.text_content() or "EMAIL" in row.text_content():
                continue
            citation, date, name = row.text_content().split(",", 2)
            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "docket": "",
                    "url": row.findall(".//a")[0].attrib["href"],
                    "citation": citation,
                }
            )
