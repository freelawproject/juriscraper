"""Scraper for the Arkansas Attorney General
CourtID: arkag
Court Short Name: Arkansas Attorney General
"""

import difflib
import re
from datetime import date
from typing import Any, cast
from urllib.parse import urljoin

from typing_extensions import override

from juriscraper.lib.exceptions import ParsingException
from juriscraper.OpinionSite import ExtractedMetaData
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

# Letters-only keys of the people who sign, not the deputy who prepared the draft.
_SIGNERS = {
    "DUSTINMCDANIEL": ("DUSTIN McDANIEL", "Attorney General"),
    "LESLIERUTLEDGE": ("LESLIE RUTLEDGE", "Attorney General"),
    "TIMGRIFFIN": ("TIM GRIFFIN", "Attorney General"),
    # https://opinionstorage.blob.core.windows.net/opinions/2013-078.pdf
    "BRADFORDJPHELPS": ("BRADFORD J. PHELPS", "Chief Deputy Attorney General"),
    # https://opinionstorage.blob.core.windows.net/opinions/2026-118.pdf
    "ZACHMAYO": ("ZACH MAYO", "Chief Deputy Attorney General"),
}


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
                    "date_filed_is_approximate": True,
                    "url": hit["PDFUrl"].split("?")[0],
                    "summary": self._summary(hit),
                }
            )

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetaData:
        text = (
            scraped_text.replace("\r\n", "\n")
            .replace("\r", "\n")
            .replace("\u00a0", " ")
        )
        closing = re.search(r"(?im)^[ \t]*sincerely\b.*$", text)
        if not closing:
            return {}
        tail = text[closing.end() : closing.end() + 400]
        title = re.search(
            r"(?im)^[ \t]*((?:chief deputy )?attorney general)\b",
            tail,
        )
        if not title:
            return {}
        lines = [
            line.strip()
            for line in tail[: title.start()].splitlines()
            if re.search(r"[A-Za-z]", line)
        ]
        if not lines:
            return {}
        key = "".join(ch for ch in lines[-1].upper() if ch.isalpha())
        signer = _SIGNERS.get(key)
        if signer is None and key:
            near = difflib.get_close_matches(key, _SIGNERS, n=1, cutoff=0.85)
            signer = _SIGNERS[near[0]] if near else None
        if not signer:
            return {}
        role = re.sub(r"\s+", " ", title.group(1)).casefold()
        if signer[1].casefold() != role:
            return {}
        return {"OpinionCluster": {"judges": f"{signer[0]}, {signer[1]}"}}
