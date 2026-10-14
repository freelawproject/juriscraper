"""Scraper for Supreme Court of Northern Mariana Islands
CourtID: nmi
Court Short Name: NMI
Author: William Edward Palin
History:
  2023-01-21: Created by William Palin
  2026-09-24: Site moved to cnmilaw.gov; use urllib to pass Cloudflare
"""

import re
from datetime import date
from urllib.parse import urljoin

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, normalize_dashes
from juriscraper.lib.type_utils import ExtractedMetadata
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    use_urllib = True  # Use urllib to pass Cloudflare

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        year = date.today().year
        self.url = f"https://cnmilaw.gov/documents?type=case&court=Supreme&year={year}"
        self.status = "Published"

    def _cleanup_judge_names(self, judges: str) -> list[str]:
        """Extract judge panel

        Because of a judge Torres,Jr. - and the various permutations of his
        Jr with and without commas and spacing we do a bit of cleanup to
        get his and the other judges corretly.  Additionally the author is
        sometimes denoted by a *.  This is cleaned up.

        :param judges: Content of the panel as a string
        :return: Judges as a string list
        """
        judge_list = judges.split(",")
        judge_list = [j.replace(" Jr.", "Jr.").strip(" *") for j in judge_list]
        judge_list = [j.replace("Jr.", " Jr.") for j in judge_list]
        return judge_list

    def _fetch_author(self, judges: str) -> str:
        """Parse the author from the judge text

        :param judges: Cell content
        :return: The author
        """
        if "*" not in judges:
            author = ""
        else:
            author = [j for j in judges.split(",") if "*" in j][0].strip("*")
        return author

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            ".//a[@class='pdf-link']/ancestor::tr"
        )
        for s in elements:
            cells = s.findall(".//td")
            judge_text = cells[3].text_content()
            author = self._fetch_author(judge_text)
            url: str = s.xpath(".//a[@class='pdf-link']/@href")[0]
            self.cases.append(
                {
                    "name": cells[0].text_content(),
                    # Source renders neutral cites as "YYYY-MP-NN"; eyecite/
                    # reporters-db expect spaces (e.g. "2022 MP 09"). #1947
                    "citation": cells[1].text_content().replace("-", " "),
                    "date": cells[2].text_content(),
                    "judge": ", ".join(self._cleanup_judge_names(judge_text)),
                    "author": author,
                    "per_curiam": not bool(author),
                    "url": urljoin(
                        (self.url if self.url is not None else ""),
                        url,
                    ),
                    "docket": "",
                }
            )

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Pass scraped text into function and return data as a dictionary

        :param scraped_text: Text of scraped content
        :return: metadata containing the docket number
        """
        normalized_content = normalize_dashes(scraped_text)
        match = re.findall(r"Case No\.: (.*)", normalized_content)
        docket_number = match[0] if bool(match) else ""
        metadata: ExtractedMetadata = {
            "Docket": {
                "docket_number": docket_number,
            },
        }
        return metadata
