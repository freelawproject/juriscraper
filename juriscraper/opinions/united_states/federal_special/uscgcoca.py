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

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.citation_regex = r"(?P<MJ>\(?\d{2} M\.?J\.? \d+\)?)|(?P<WL>\(?\d{4} (W\.?[Ll]\.?) \d+\)?)"
        self.case_name_regex = r"^(?P<case_name>.*?)\s*(?:-\s*(?:Unpublished|Published)|(?:\s*\([^)]*(?:WL|MERITS|UNPUBLISHED)[^)]*\))|(?:\s*\(UNPUBLISHED\))|(?:\s*-\s*UNPUBLISHED))\s*$"
        self.base_url = self.url = (
            "https://www.uscg.mil/Resources/Legal/Court-of-Criminal-Appeals/CGCCA-Opinions/"
        )
        self.request["headers"] = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=0, i",
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        }
        self.needs_special_headers = True

        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Process the HTML

        :return: None
        """
        path = "//table[@class='Dashboard']/tbody/tr"
        for item in self.html.xpath(path):
            url = item.xpath(".//td/a/@href")[0]
            first_cell = item.xpath(".//td/a/text()")[0]
            docket = re.sub(
                r"Docket Nos?\.", "", item.xpath(".//td[2]/text()")[0]
            )
            date_string = item.xpath(".//td[3]/text()")[0]
            m = re.search(self.citation_regex, first_cell)
            if m:
                mj = m.group("MJ").strip("()") if m.group("MJ") else ""
                wl = m.group("WL").strip("()") if m.group("WL") else ""
            else:
                mj = ""
                wl = ""

            match = re.match(self.case_name_regex, first_cell)
            if match:
                first_cell = (
                    match.group("case_name").strip().replace("II", "2nd")
                )

            status = "Published" if m and mj else "Unpublished"

            self.cases.append(
                {
                    "name": first_cell,
                    "date": date_string,
                    "docket": docket,
                    "url": url,
                    "status": status,
                    "citation": mj,
                    "parallel_citation": wl,
                }
            )

    def _download_backwards(self, page_number: int) -> None:
        """Method used by backscraper to download historical records

        :param page_number: an element of self.back_scrape_iterable
        :return: None
        """
        self.url = f"{self.base_url}?smdpage15701={page_number}"

    def _get_case_names(self) -> list[str]:
        """Clean case names

        :return: List of case names
        """
        for case in self.cases:
            if case["citation"]:
                case["name"] = re.sub(
                    rf"\(?\s?{case['citation']}\s?\)?",
                    "",
                    case["name"],
                )
            if case["parallel_citation"]:
                case["name"] = re.sub(
                    rf"\(?\s?{case['parallel_citation']}\s?\)?",
                    "",
                    case["name"],
                )
            case["name"] = re.sub(
                r"\(UNPUBLISHED\)|\(MERITS\)|\(PER CURIAM\)|ORDER",
                "",
                case["name"],
                flags=re.IGNORECASE,
            )
            case["name"] = titlecase(case["name"].strip(" -"))

        return [c["name"] for c in self.cases]

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Checks if backscrape start and end arguments have been passed"""

        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start is None or not str(start).isdigit():
            # There are 34 historical pages as of development in Jun 2025
            start = 34
        if end is None or not str(end).isdigit():
            end = 1

        self.back_scrape_iterable = range(int(start), int(end) - 1, -1)
