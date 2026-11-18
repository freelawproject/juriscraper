"""Scraper for the Arkansas Attorney General
CourtID: arkag
Court Short Name: Arkansas Attorney General
"""

import re
from datetime import date, timedelta
from typing import Any, cast
from urllib.parse import urljoin

from httpx import Response
from typing_extensions import override

from juriscraper.lib.exceptions import ParsingException
from juriscraper.OpinionSite import ExtractedMetaData
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    home_url = "https://prod.opinions-search.arkansasag.gov/"
    index_name = "opinions"
    # CourtListener's Columbia import covers opinions through 2011.
    # 1984 is where the Arkansas site's data starts.
    first_opinion_date = date(2012, 1, 1)
    days_interval = 100
    _bundle_re = re.compile(r'<script[^>]+src="([^"]+\.js)"', re.I)
    # Read from that bundle. A non-meilisearch.io host needs this updated.
    _credentials_re = re.compile(
        r'"(https://[^"]+\.meilisearch\.io)"\s*,\s*'
        r'(?:[A-Za-z_$][\w$]*\s*=\s*)?"([^"\s]{20,})"'
    )
    _closing_candidate_re = re.compile(r"(?mi)^ *Sincer[a-z0-9]* *[,.]? *$")
    _enclosure_re = re.compile(
        r"(?mi)^ *(?:Enclosures?|Attachments?) *[.:]? *$"
    )
    _signing_title_re = re.compile(
        r"(?mi)^ *(?:[A-Z]+ ){0,4}(?:Attorney|Solicitor) General *$"
    )
    _byline_re = re.compile(r"(?mi)^ *(?:By|For|Signed(?: by)?) *:")
    _reference_line_re = re.compile(
        r"^ *[A-Z]{2}[/:](?:[A-Z. ]{1,14}[/:])?[a-z]{1,6} *$"
    )
    _partial_name_re = re.compile(
        r"(?i)([A-Z]{3,}) ([A-Z]{5,})(?: [,./~_<>\-]{3,}[A-Z]?)?"
    )
    _docket_heading_re = re.compile(r"opinionno\.?:?(\d{2,4})-(\d{1,5})")
    _delegation_re = re.compile(
        r"(?i)\b(?:delegat\w*|recus\w*|acting\s+attorney\s+general|on\s+behalf)\b"
    )
    # Verified against the PDF signature blocks in the extraction fixtures.
    # OCR can truncate a name or mistake handwriting for text. Prefer exact
    # names; limited suffix recovery requires independent primary evidence.
    _signatories = {
        "dustinmcdaniel": ("DUSTIN McDANIEL", "Attorney General"),
        # Explicit OCR spellings of 2012-009, not approximate name matching.
        "dustinm&daniel": ("DUSTIN McDANIEL", "Attorney General"),
        "dustinm@&daniel": ("DUSTIN McDANIEL", "Attorney General"),
        "leslierutledge": ("LESLIE RUTLEDGE", "Attorney General"),
        "timgriffin": ("TIM GRIFFIN", "Attorney General"),
        # https://opinionstorage.blob.core.windows.net/opinions/2013-078.pdf
        "bradfordj.phelps": (
            "BRADFORD J. PHELPS",
            "Chief Deputy Attorney General",
        ),
        "zachmayo": ("ZACH MAYO", "Chief Deputy Attorney General"),
    }

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
        # Discovery requests must not inherit the search JSON or bearer token.
        headers = self.request["headers"]
        parameters = self.request["parameters"]
        self.request["headers"] = {
            key: value
            for key, value in headers.items()
            if key.lower() not in {"authorization", "accept", "content-type"}
        }
        self.request["parameters"] = {}
        try:
            await self._request_url_get(url)
            response = cast(Response, self.request["response"])
            response.raise_for_status()
            return response.text
        finally:
            self.request["headers"] = headers
            self.request["parameters"] = parameters

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
        method = self.method
        headers = self.request["headers"]
        parameters = self.request["parameters"]
        self.method = "POST"
        self.request["parameters"] = {
            **parameters,
            "json": self._search_payload(),
        }
        self.request["headers"] = {
            **headers,
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        try:
            return await super()._download(request_dict)
        finally:
            self.method = method
            self.request["headers"] = headers
            self.request["parameters"] = parameters

    @override
    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        self.results_limit = 1000
        start, end = dates
        # Framework ranges include both dates; the API's upper bound excludes it.
        exclusive_end = end + timedelta(days=1)
        self.opinion_filter = (
            f'Date_Published >= "{start.isoformat()}" AND '
            f'Date_Published < "{exclusive_end.isoformat()}"'
        )
        self.html = await self._download()
        response = cast(dict[str, Any], self.html)
        hits = response["hits"]
        # Meilisearch caps accessible results. Never silently accept a clipped
        # interval; callers can reduce days_interval rather than lose opinions.
        if len(hits) >= self.results_limit or response.get(
            "estimatedTotalHits", len(hits)
        ) > len(hits):
            raise ParsingException(
                "arkag: backscrape results may be truncated; reduce days_interval"
            )
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
            # A PDF page break need not include a newline. Make a closing at
            # the top of an attached page visible to the ambiguity check.
            .replace("\f", "\n\f\n")
        )
        text = re.sub(r"[ \t]+", " ", text)
        closings = list(self._closing_candidate_re.finditer(text))
        # Damaged or additional closings make document boundaries uncertain.
        if len(closings) != 1:
            return {}
        closing = closings[0]
        if self._key(closing.group()) not in {
            "sincerely",
            "sincerely,",
        }:
            return {}
        enclosure = self._enclosure_re.search(text)
        if enclosure and enclosure.start() < closing.start():
            return {}

        # One title anchors the entire closing page, including primary footnotes.
        page = text[closing.end() :].split("\f", 1)[0]
        titles = list(self._signing_title_re.finditer(page))
        if len(titles) != 1 or self._byline_re.search(page):
            return {}
        title = titles[0]
        if title.end() > 400 or self._enclosure_re.search(
            page[: title.start()]
        ):
            return {}
        for line in page[title.end() :].splitlines():
            if re.match(r"^ *\d+(?: |$)", line):
                break
            if self._enclosure_re.fullmatch(
                line
            ) or self._reference_line_re.fullmatch(line):
                continue
            if any(character.isalnum() for character in line):
                return {}

        # The printed name must be immediately above its title (up to two blanks).
        before = page[: title.start()]
        trimmed = before.rstrip(" \t\n")
        if before[len(trimmed) :].count("\n") > 3:
            return {}
        ink, _, name = trimmed.rpartition("\n")
        name = name.strip(" \t")
        role = title.group().strip().casefold()
        signer = self._signatories.get(self._key(name))
        if signer and signer[1].casefold() != role:
            signer = None
        if not signer:
            # A header can complete a substantial suffix loss, never supply a name.
            fragment = self._partial_name_re.fullmatch(name)
            if (
                not fragment
                or role != "attorney general"
                or any(character.isalnum() for character in ink)
                or self._delegation_re.search(text)
            ):
                return {}
            prefix = " ".join(fragment.groups()).casefold()
            candidates = [
                candidate
                for candidate in set(self._signatories.values())
                if candidate[1] == "Attorney General"
                and candidate[0].casefold().startswith(prefix)
                and len(candidate[0]) - len(prefix) <= 3
            ]
            if len(candidates) != 1 or not self._header_matches(
                text, closing.start(), candidates[0][0]
            ):
                return {}
            signer = candidates[0]
        return {"OpinionCluster": {"judges": f"{signer[0]}, {signer[1]}"}}

    @staticmethod
    def _key(value: str) -> str:
        return re.sub(r"[ \t]", "", value).casefold()

    def _header_matches(
        self, text: str, closing_start: int, name: str
    ) -> bool:
        """Require a complete primary header and consistent preceding headings."""

        def rows(value: str) -> list[str]:
            return [
                self._key(line) for line in value.splitlines() if line.strip()
            ]

        first_page = rows(text.partition("\f")[0])
        if len(first_page) < 4:
            return False
        header = first_page[:3]
        docket = self._docket_heading_re.fullmatch(first_page[3])
        if (
            not docket
            or header[0] != "stateofarkansas"
            or header[1] not in {"attorneygeneral", "theattorneygeneral"}
            or header[2] != self._key(name)
        ):
            return False
        preceding = rows(text[:closing_start])
        dockets = {
            tuple(map(int, match.groups()))
            for line in preceding
            if (match := self._docket_heading_re.fullmatch(line))
        }
        return dockets == {tuple(map(int, docket.groups()))} and all(
            preceding[index : index + 3] == header
            for index, line in enumerate(preceding)
            if line == "stateofarkansas"
        )
