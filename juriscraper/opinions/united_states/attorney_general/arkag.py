"""Scraper for the Arkansas Attorney General
CourtID: arkag
Court Short Name: Arkansas Attorney General
"""

import re
from datetime import date
from typing import Any, cast
from urllib.parse import urljoin

from typing_extensions import override

from juriscraper.lib.exceptions import ParsingException
from juriscraper.OpinionSite import ExtractedMetaData
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    home_url = "https://prod.opinions-search.arkansasag.gov/"
    index_name = "opinions"
    # CourtListener's Columbia import covers opinions through 2011.
    # 1984 is where the Arkansas site's data starts.
    first_opinion_year = 2012
    _bundle_re = re.compile(r'<script[^>]+src="([^"]+\.js)"', re.I)
    # Read from that bundle. A non-meilisearch.io host needs this updated.
    _credentials_re = re.compile(
        r'"(https://[^"]+\.meilisearch\.io)"\s*,\s*'
        r'(?:[A-Za-z_$][\w$]*\s*=\s*)?"([^"\s]{20,})"'
    )
    # Name must start the line. A leading ^.*? also matched letterhead
    # when the closing "Sincerely" was missing (89-178).
    _signature_re = re.compile(
        r"(?m)^[ \t]*"
        r"([A-Z][A-Za-z'’.\-]*(?:[ \t]+[A-Z][A-Za-z'’.\-]*){1,4})"
        r"[ \t]*\n(?:[ \t]*\n){0,2}[ \t]*"
        r"((?i:(?:Chief Deputy )?Attorney General))"
        r"(?:[ \t]*$|(?=[A-Z]))"
    )
    # fmt: off
    _non_name_tokens = frozenset({
        "ARKANSAS", "ATTORNEY", "DEPARTMENT", "GENERAL", "HONORABLE",
        "OFFICE", "OF", "OPINION", "PAGE", "STATE", "THE",
    })
    # fmt: on

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.home_url
        self.status = "Published"
        self.should_have_results = True
        # Azure serves these PDFs as application/octet-stream.
        self.expected_content_types = [
            "application/pdf",
            "application/octet-stream",
        ]
        self.results_limit = 10
        self.opinion_filter = None
        self.parameters = {}
        self.make_backscrape_iterable(kwargs)

    @override
    def make_backscrape_iterable(self, kwargs: dict) -> None:
        # Plain years, both ends inclusive: --backscrape-start 2012.
        start = kwargs.get("backscrape_start") or self.first_opinion_year
        end = kwargs.get("backscrape_end") or date.today().year
        self.back_scrape_iterable = list(range(int(start), int(end) + 1))

    def _search_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "q": "",
            "limit": self.results_limit,
            "sort": ["Date_Published:desc"],
            "attributesToRetrieve": [
                "OpenFileNo",
                "Date_Published",
                "RequestorNameFull",
                "OpinionSummary",
                "PDFUrl",
            ],
        }
        if self.opinion_filter:
            payload["filter"] = self.opinion_filter
        return payload

    async def _fetch_text(self, url: str) -> str:
        response = await self.request["session"].get(
            url, headers=self.request["headers"], timeout=60
        )
        response.raise_for_status()
        return response.text

    async def _fetch_credentials(self) -> tuple[str, str]:
        page = await self._fetch_text(self.home_url)
        for src in self._bundle_re.findall(page):
            script = await self._fetch_text(urljoin(self.home_url, src))
            if match := self._credentials_re.search(script):
                return match.group(1), match.group(2)
        raise ParsingException(
            "arkag: could not find the Meilisearch search key"
        )

    @override
    async def _download(self, request_dict=None):
        if self.test_mode_enabled():
            return await super()._download(request_dict)

        host, api_key = await self._fetch_credentials()
        self.url = f"{host}/indexes/{self.index_name}/search"
        self.method = "POST"
        self.request["parameters"]["json"] = self._search_payload()
        self.request["headers"]["Authorization"] = f"Bearer {api_key}"
        self.request["headers"]["Accept"] = "application/json"
        return await super()._download(request_dict)

    @override
    async def _download_backwards(self, year: int) -> None:
        # Both prefixes. The largest year is under 500, so limit 1000.
        self.results_limit = 1000
        self.opinion_filter = (
            f'OpenFileNo STARTS WITH "{year}-" OR '
            f'OpenFileNo STARTS WITH "{year % 100:02d}-"'
        )
        self.html = await self._download()
        self._process_html()

    @staticmethod
    def _summary(hit: dict[str, Any]) -> str:
        requester = hit["RequestorNameFull"].strip()
        sep = "" if requester.endswith(".") else "."
        return f"Requester: {requester}{sep} {hit['OpinionSummary']}"

    @override
    def _process_html(self) -> None:
        response = cast(dict[str, Any], self.html)
        for hit in response["hits"]:
            docket = hit["OpenFileNo"]
            self.cases.append(
                {
                    "docket": docket,
                    "name": f"Arkansas Attorney General Opinion No. {docket}",
                    "date": hit["Date_Published"].split("T", 1)[0],
                    "url": hit["PDFUrl"].split("?")[0],
                    "summary": self._summary(hit),
                }
            )

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetaData:
        # First name after the last Sincerely. Without that close, the
        # only match is the letterhead (89-178).
        text = (
            scraped_text.replace("\r\n", "\n")
            .replace("\r", "\n")
            .replace("\u00a0", " ")
        )
        sincerely = text.lower().rfind("sincerely")
        if sincerely == -1:
            return {}
        matches = [
            match
            for match in self._signature_re.finditer(text)
            if match.start() > sincerely
            and self._is_signature_name(match.group(1))
        ]
        if not matches:
            return {}

        name = re.sub(r"\s+", " ", matches[0].group(1)).strip(" .,")
        title = re.sub(r"\s+", " ", matches[0].group(2)).strip().casefold()
        office = (
            "Chief Deputy Attorney General"
            if title == "chief deputy attorney general"
            else "Attorney General"
        )
        return {"OpinionCluster": {"judges": f"{name}, {office}"}}

    @classmethod
    def _is_signature_name(cls, raw_name: str) -> bool:
        tokens = {token.strip(".").upper() for token in raw_name.split()}
        return bool(tokens) and not tokens & cls._non_name_tokens
