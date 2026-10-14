"""Scraper for US Coast Guard Court of Criminal Appeals
CourtID: cgcca
Court Short Name: C.G. Ct. Crim. App.

Author: Evando Blanco
Reviewer: flooie
History:
    2021-03-29: Created by Evando Blanco
    2021-12-17: Updated by flooie for OpinionSiteLinear
    2025-06-11: Updated by lmanzur to add backscraping support
"""

import re
from collections.abc import Mapping
from urllib.parse import urljoin

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.lib.type_utils import RawOpinion
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[int]):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.citation_regex = r"(?P<MJ>[\(\[]?\d{2} M\.?J\.?\.?\s*\d+[\)\]]?)|(?P<WL>[\(\[]?\d{4} W\.?L\.?\.?\s*\d+[\)\]]?)"
        self.base_url = self.url = (
            "https://www.uscg.mil/Resources/Legal/Court-of-Criminal-Appeals/CGCCA-Opinions/"
        )
        self.request["headers"] = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=0, i",
            "sec-ch-ua": self.chrome_sec_ch_ua,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "cross-site",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": self.chrome_user_agent,
        }
        self.needs_special_headers = True
        self.should_have_results = True

        self.make_backscrape_iterable(kwargs)

    @override
    def _process_html(self) -> None:
        """Process the HTML

        :return: None
        """
        path = "//table[@class='Dashboard']/tbody/tr"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        items: list[HtmlElement] = self.html.xpath(path)
        for item in items:
            url: str = item.xpath(".//td/a/@href")[0]
            first_cell: str = item.xpath(".//td/a/text()")[0]
            tds = item.findall(".//td")
            summary = ""
            per_curiam = False

            # Different table structure for recent vs older opinions
            if len(tds) > 3:
                docket = re.sub(r"Docket Nos?\.", "", tds[3].text_content())
                summary = tds[2].text_content()
                per_curiam = "per curiam" in summary.lower()
                date_string = tds[5].text
            else:
                docket = re.sub(r"Docket Nos?\.", "", tds[1].text_content())
                date_string = tds[2].text

            m = re.search(self.citation_regex, first_cell)
            if m is not None:
                mj = m.group("MJ").strip("()") if bool(m.group("MJ")) else ""
                wl = m.group("WL").strip("()") if bool(m.group("WL")) else ""
            else:
                mj = ""
                wl = ""

            status = (
                "Published" if (m is not None and bool(mj)) else "Unpublished"
            )

            self.cases.append(
                self.clean_case_name(
                    {
                        "name": first_cell,
                        "date": date_string,
                        "docket": docket,
                        "url": url,
                        "status": status,
                        "citation": mj,
                        "parallel_citation": wl,
                        "summary": summary,
                        "per_curiam": per_curiam,
                    }
                )
            )

    @override
    async def _download_backwards(self, page_number: int) -> None:
        """Method used by backscraper to download historical records

        :param page_number: an element of self.back_scrape_iterable
        :return: None
        """
        self.url = urljoin(self.base_url, f"?smdpage15701={page_number}")

    @staticmethod
    def clean_case_name(case: RawOpinion) -> RawOpinion:
        """Clean case name by removing citations and unnecessary text

        :param case: A dictionary containing case information
        :return dict: The updated case dictionary with a cleaned case name
        """
        if "name" not in case:
            raise KeyError("name")
        name = case["name"]

        for citation in [case.get("citation"), case.get("parallel_citation")]:
            if bool(citation) and citation in name:
                name = name.split(citation, 1)[0]

        parts: list[str] = re.split(
            r"[(-]| WITH | ONREMAND | PETITION FOR", name
        )
        if len(parts) > 1 and parts[0].strip().lower() in [
            "order",
            "opinion",
            "petition",
        ]:
            name = parts[1].strip()
        else:
            name = parts[0].strip()

        name = re.sub(r"^order\s*:?[\s-]*", "", name, flags=re.IGNORECASE)
        name = re.sub(
            r"\b(opinion|petition|petition order)\b\s*$",
            "",
            name,
            flags=re.IGNORECASE,
        )

        case["name"] = titlecase(name.strip(" -:"))
        return case

    @override
    def make_backscrape_iterable(self, kwargs: Mapping[str, object]) -> None:
        """Checks if backscrape start and end arguments have been passed"""

        start = str(kwargs.get("backscrape_start"))
        end = str(kwargs.get("backscrape_end"))

        if not start.isdigit():
            start = "1"
        if not end.isdigit():
            # There are 34 historical pages as of development in Jun 2025
            end = "34"

        self.back_scrape_iterable = range(int(end), int(start) - 1, -1)
