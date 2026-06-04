# Scraper for Louisiana Supreme Court
# CourtID: la
# Court Short Name: LA
# Contact: Community relations department
#          Robert Gunn
#          504-310-2592
#          rgunn@lasc.org

import asyncio
import json
import re
from urllib.parse import urljoin

import httpx

from juriscraper.AbstractSite import logger
from juriscraper.lib.exceptions import ParsingException
from juriscraper.lib.html_utils import get_html_parsed_text
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

# SignalR record separator (used between text frames such as the handshake)
RECORD_SEPARATOR = b"\x1e"


class Site(OpinionSiteLinear):
    """Louisiana Supreme Court.

    Since early 2026 lasc.org is a Blazor Server application (#1983): the
    Court Actions content is rendered client-side over a SignalR circuit, so a
    plain GET returns only the JavaScript shell with no opinions. The legacy
    http:// host is dead (returns 521) and there is no REST/JSON API.

    We therefore, without a browser:
      1. read the RSS feed to list the most recent "Opinions" sub-pages
      2. drive the Blazor circuit for each sub-page to obtain the rendered
         news-release HTML
      3. parse that HTML -- its markup is identical to the legacy
         ``textarea#PostContent`` content, so the original parsing applies

    Driving the circuit is inherently coupled to Blazor internals; if the site
    framework changes this will need to be revisited.
    """

    base_url = "https://www.lasc.org"
    rss_url = "https://www.lasc.org/rss"
    # Most recent "Opinions" sub-pages to render per run. The regular scrape
    # only needs the latest handful; CL dedupes already-seen opinions.
    max_subpages = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = self.rss_url
        # (url, rendered news-release HTML) pairs, compiled into a single
        # archivable response for save_response after processing (#1983).
        self.rendered_pages: list[tuple[str, str]] = []
        # lasc.org sits behind Cloudflare and serves the default httpx
        # User-Agent the 521/empty shell more often; a browser UA is stabler.
        self.request["headers"]["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )

    async def _download(self, request_dict=None):
        if self.test_mode_enabled():
            # The example file is a single rendered news-release fragment.
            return [await OpinionSiteLinear._download(self, request_dict)]

        self.rendered_pages = []
        for url in await self._get_recent_opinion_subpages():
            fragment = await self._render_blazor_page(url)
            self.rendered_pages.append((url, fragment))
        return [get_html_parsed_text(html) for _, html in self.rendered_pages]

    def _process_html(self):
        xpath = "//a[contains(@href, 'opinions') and contains(@href, 'pdf')]"
        for html in self.html:
            date_string = self._get_date_for_opinions(html)
            for anchor in html.xpath(xpath):
                text = anchor.text_content()
                parts = text.split(None, 1)
                if len(parts) < 2:
                    logger.warning(
                        "la: opinion link without a case name: %s", text
                    )
                    continue

                judge = self._get_judge_above_anchor(anchor)
                per_curiam = False
                if judge and "per curiam" in judge.lower():
                    per_curiam = True
                    judge = ""

                self.cases.append(
                    {
                        "date": date_string,
                        "docket": parts[0],
                        "judge": judge or "",
                        "per_curiam": per_curiam,
                        "name": titlecase(parts[1]),
                        "disposition": self._get_disposition(anchor, text),
                        "url": urljoin(self.base_url, anchor.get("href")),
                    }
                )

        self._compile_response()

    def _get_disposition(self, anchor, anchor_text: str) -> str:
        """Extract and tidy the disposition that follows the opinion link.

        The link's paragraph reads like
        ``(Parish of X) AFFIRMED AND REMANDED. SEE OPINION.``; drop the parish
        prefix and the trailing "SEE ..." directive, and titlecase the rest.

        :param anchor: the opinion link element
        :param anchor_text: the link text (docket + name) to strip from the
            surrounding text nodes
        :return: the cleaned disposition, e.g. "Affirmed and Remanded"
        """
        text = " ".join(anchor.getparent().xpath("./text()")).replace(
            anchor_text, ""
        )
        text = re.sub(r"\(Parish of [^)]*\)", "", text)
        text = re.sub(r"\bSEE\b.*$", "", text, flags=re.S)
        return titlecase(" ".join(text.split()))

    def _compile_response(self) -> None:
        """Expose the rendered sub-pages as a single archivable response.

        The circuit makes several internal requests per sub-page (shell,
        negotiate, handshake, StartCircuit, render-batch polls) that bypass
        AbstractSite's per-request ``save_response`` hook. We concatenate the
        rendered news releases into one HTML document, assign it as
        ``self.request["response"]``, and invoke the ``save_response`` hook
        ourselves so the scrape still yields a single response for
        auditing/debugging on S3 (#1983).
        """
        if self.test_mode_enabled() or not self.rendered_pages:
            return

        document = "\n".join(
            f"<!-- {url} -->\n{fragment}"
            for url, fragment in self.rendered_pages
        )
        self.request["url"] = self.url
        self.request["response"] = httpx.Response(
            status_code=200,
            headers={"Content-Type": "text/html; charset=utf-8"},
            content=document.encode("utf-8"),
            request=httpx.Request("GET", self.url),
        )

        # The base class only calls this from its own request methods, which
        # the circuit bypasses, so trigger it here.
        if self.save_response:
            self.save_response(self)

    async def _get_recent_opinion_subpages(self) -> list[str]:
        """Read the RSS feed and return recent Opinions sub-page URLs.

        RSS items look like::

            <title>Opinions - Court Actions June 1, 2026</title>
            <link>https://www.lasc.org/Opinions?p=2026-025</link>

        :return: list of absolute sub-page URLs, most recent first
        :raises ParsingException: if the feed has no ``<item>`` entries at
            all, which means its format changed and the scrape should fail
            rather than silently yield no opinions
        """
        raw = await self._get_with_retries(self.rss_url)
        if "<item>" not in raw:
            raise ParsingException(
                f"la: no <item> entries in RSS feed {self.rss_url}; "
                "the feed format may have changed"
            )

        item_re = re.compile(
            r"<item>.*?<title>(?P<title>.*?)</title>.*?"
            r"<link>(?P<link>.*?)</link>",
            re.S,
        )
        matches = list(item_re.finditer(raw))
        if not matches:
            # <item> entries exist but the title/link layout changed
            raise ParsingException(
                f"la: RSS feed {self.rss_url} has <item> entries but none "
                "matched the expected title/link format"
            )

        urls = [
            match.group("link").strip()
            for match in matches
            if match.group("title").strip().startswith("Opinions")
        ]
        if not urls:
            # Could be a quiet stretch with only non-opinion news, so warn
            # rather than crash; recurring warnings mean the titles changed
            logger.warning(
                "la: no 'Opinions' items in RSS feed %s", self.rss_url
            )
        return urls[: self.max_subpages]

    async def _render_blazor_page(self, url: str) -> str:
        """Drive the Blazor Server circuit and return the rendered news release.

        :param url: the Opinions sub-page URL
        :return: the news-release HTML fragment
        :raises ParsingException: if the page has no Blazor components or the
            circuit yields no opinion content; both mean the site changed and
            should fail the scrape rather than silently drop opinions
        """
        session = self.request["session"]
        markers, app_state = await self._get_blazor_shell(url)
        if not markers:
            raise ParsingException(
                f"la: no Blazor components in shell for {url}"
            )

        octet = {"Content-Type": "application/octet-stream"}
        negotiate = await session.post(
            urljoin(self.base_url, "/_blazor/negotiate?negotiateVersion=1"),
            content=b"",
            headers=self.request["headers"],
        )
        # Surface a clear HTTP error instead of a JSONDecodeError below
        negotiate.raise_for_status()
        token = negotiate.json()["connectionToken"]
        conn_url = urljoin(self.base_url, f"/_blazor?id={token}")

        # SignalR handshake (always JSON, even for the blazorpack protocol)
        handshake = json.dumps({"protocol": "blazorpack", "version": 1})
        await session.post(
            conn_url,
            content=handshake.encode() + RECORD_SEPARATOR,
            headers=octet,
        )

        # Invoke the StartCircuit hub method to begin server rendering.
        invocation = self._encode_start_circuit(
            f"{self.base_url}/", url, json.dumps(markers), app_state
        )
        await session.post(conn_url, content=invocation, headers=octet)

        # Long-poll for render batches; the news release arrives in the first
        # non-empty batch, so stop as soon as we can extract it. Any httpx
        # error here is allowed to bubble up and fail the scrape.
        collected = bytearray()
        for _ in range(12):
            response = await session.get(conn_url, timeout=30)
            collected += response.content
            fragment = self._extract_news_release(bytes(collected))
            if fragment is not None:
                return fragment

        raise ParsingException(f"la: no rendered opinion content for {url}")

    async def _get_blazor_shell(self, url: str) -> tuple[list[dict], str]:
        """Load the Blazor shell and extract its component markers and state.

        :param url: the page URL whose shell to load
        :return: (server component markers, serialized application state)
        """
        raw = await self._get_with_retries(url)
        markers = []
        for marker in re.findall(r"<!--Blazor:(\{.*?\})-->", raw, re.S):
            try:
                data = json.loads(marker)
            except json.JSONDecodeError:
                continue
            if data.get("type") == "server":
                markers.append(
                    {
                        "type": data["type"],
                        "sequence": data["sequence"],
                        "descriptor": data["descriptor"],
                    }
                )
        state_match = re.search(
            r"<!--Blazor-Server-Component-State:(.*?)-->", raw, re.S
        )
        app_state = state_match.group(1).strip() if state_match else ""
        return markers, app_state

    async def _get_with_retries(self, url: str, retries: int = 8) -> str:
        """GET a URL, retrying through lasc.org's intermittent 521 errors.

        Backs off exponentially between attempts (1, 2, 4 ... capped at 16
        seconds), since the 521s do not clear immediately.

        :param url: the URL to fetch
        :param retries: number of attempts
        :return: the response text
        :raises httpx.HTTPError: if every attempt failed; this should bubble
            up and fail the scrape rather than silently yielding no opinions
        """
        session = self.request["session"]
        error = httpx.HTTPError(f"la: no response from {url}")
        for attempt in range(retries):
            try:
                response = await session.get(
                    url, headers=self.request["headers"], timeout=30
                )
                response.raise_for_status()
                return response.text
            except httpx.HTTPError as exc:
                error = exc
                if attempt < retries - 1:
                    await asyncio.sleep(min(2**attempt, 16))
        raise error

    @staticmethod
    def _extract_news_release(render_bytes: bytes) -> str | None:
        """Recover the rendered news-release HTML from Blazor render batches.

        The news release is rendered as a single raw-markup string, so it
        survives intact inside the render batch's string table. We scan for the
        printable run that contains an opinion PDF link.

        :param render_bytes: accumulated bytes from the circuit
        :return: the news-release HTML fragment, or None
        """
        printable = re.findall(
            rb"[\x09\x0a\x0d\x20-\x7e\x80-\xff]{4,}", render_bytes
        )
        for chunk in printable:
            text = chunk.decode("utf-8", "replace")
            if ".pdf" in text.lower() and (
                "nrbody" in text.lower() or "/opinions" in text.lower()
            ):
                return text
        return None

    @staticmethod
    def _encode_start_circuit(
        base_uri: str, uri: str, components: str, app_state: str
    ) -> bytes:
        """Encode the ``StartCircuit`` SignalR invocation as a blazorpack frame.

        blazorpack is MessagePack with a 7-bit varint length prefix. We only
        ever send this one fixed-shape message, so we hand-encode it to avoid a
        ``msgpack`` dependency. The SignalR Invocation message is::

            [1, {}, "0", "StartCircuit", [baseUri, uri, components, appState], []]

        (If more message types are ever needed, depend on ``msgpack`` instead.)

        :return: the length-prefixed blazorpack frame
        """

        def pack_str(value: str) -> bytes:
            data = value.encode("utf-8")
            length = len(data)
            if length < 32:  # fixstr
                return bytes([0xA0 | length]) + data
            if length < 65536:  # str 16 (msgpack-python skips str 8)
                return b"\xda" + length.to_bytes(2, "big") + data
            return b"\xdb" + length.to_bytes(4, "big") + data  # str 32

        payload = b"".join(
            [
                b"\x96",  # fixarray, 6 elements
                b"\x01",  # message type 1 (Invocation)
                b"\x80",  # empty headers map
                pack_str("0"),  # invocation id
                pack_str("StartCircuit"),  # target
                b"\x94",  # fixarray, 4 arguments
                pack_str(base_uri),
                pack_str(uri),
                pack_str(components),
                pack_str(app_state),
                b"\x90",  # empty stream ids array
            ]
        )

        # 7-bit varint length prefix
        prefix = bytearray()
        length = len(payload)
        while True:
            byte = length & 0x7F
            length >>= 7
            if length:
                prefix.append(byte | 0x80)
            else:
                prefix.append(byte)
                break
        return bytes(prefix) + payload

    def _get_date_for_opinions(self, html) -> str:
        """Parse the hand-down date, e.g. "1st day of June, 2026".

        :param html: the parsed news-release fragment
        :return: a date string like "June 1st 2026"
        """
        spans = html.xpath("//span[@class='nrdate']") or html.xpath("//span")
        element_date_text = spans[0].text_content().strip()
        parts = element_date_text.split("day of")
        day = parts[0].split()[-1]
        month = parts[1].split()[0].strip(",")
        year = parts[1].split()[1].strip(",")
        return " ".join([month, day, year])

    def _get_judge_above_anchor(self, anchor) -> str | None:
        path = (
            "./preceding::*[starts-with(., 'BY ') or contains(., 'CURIAM:')]"
        )
        try:
            text = anchor.xpath(path)[-1].text_content()
        except IndexError:
            return None
        return text.rstrip(":").lstrip("BY").strip()

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        pattern = re.compile(
            r"""
            (?:
               On\s+Writ\s+of\s+Certiorari\s+to\s+the\s+
               |On\s+Supervisory\s+Writ\s+to\s+the\s+
            )
            (?P<lower_court>.*?)\n\s*\n
            """,
            re.X | re.DOTALL,
        )

        lower_court = ""
        if match := pattern.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()

        if lower_court:
            return {
                "Docket": {
                    "appeal_from_str": lower_court,
                }
            }

        return {}
