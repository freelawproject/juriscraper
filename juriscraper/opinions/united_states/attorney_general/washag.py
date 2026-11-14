"""Washington Attorney General opinions (AGO and AGLO).

CourtID: washag
The combined year index includes both official series, including 1970–1982.
"""

import re
from datetime import date
from urllib.parse import parse_qs, urljoin, urlsplit

from lxml import etree, html
from lxml.html import HtmlElement
from typing_extensions import override

from juriscraper.lib.exceptions import ParsingException
from juriscraper.OpinionSite import ExtractedMetaData
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.atg.wa.gov"
    docket_re = re.compile(
        r"\b(AGLO|AGO)\b.*?\b(\d{4})\s+NO\.?\s*(\d+)\b", re.I
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.today = date.today()
        self.url = self._year_url(self.today.year)
        self.status = "Published"
        self._backscraping = False
        # 1996–2011 overlaps the Columbia import, which lacks docket numbers.
        # Maintainers must reconcile those records before any ingestion there.
        self.back_scrape_iterable = [
            year
            for year in range(1949, self.today.year + 1)
            if not 1996 <= year <= 2011
        ]

    def _year_url(self, year: int) -> str:
        return f"{self.base_url}/ago-opinions/year/{year}"

    def _read_rows(self, tree: HtmlElement) -> None:
        for row in tree.xpath(
            '//div[contains(concat(" ", normalize-space(@class), " "), " views-row ")]'
        ):
            headers = row.xpath(
                './/div[contains(@class, "views-field-field-opinion-date")]'
            )
            links = row.xpath(
                './/div[contains(@class, "views-field-title")]//a'
            )
            if len(headers) != 1 or len(links) != 1:
                raise ParsingException(
                    "washag: missing opinion header or link"
                )
            match = self.docket_re.search(headers[0].text_content())
            dates = headers[0].xpath(".//time/@datetime")
            if not match or len(dates) != 1:
                raise ParsingException("washag: missing docket or exact date")
            series, year, number = match.groups()
            filed = date.fromisoformat(dates[0][:10])
            if filed.year != int(year):
                raise ParsingException(
                    "washag: docket year and filed year differ"
                )
            docket = f"{series.upper()} {year} No. {int(number)}"
            title = " ".join(links[0].text_content().split())
            href = links[0].get("href")
            target = urljoin(self.base_url, href or "")
            parsed = urlsplit(target)
            if (
                not href
                or parsed.netloc != "www.atg.wa.gov"
                or not parsed.path.startswith("/ago-opinions/")
            ):
                raise ParsingException(
                    "washag: missing or unexpected opinion URL"
                )
            self.cases.append(
                {
                    "name": f"Washington Attorney General Opinion {docket}",
                    "docket": docket,
                    "date": filed.isoformat(),
                    "url": target,
                    # The list's body is truncated, so do not use it as a headnote.
                    "summary": ""
                    if "needs title" in title.casefold()
                    else title,
                }
            )

    def _next_url(self, tree: HtmlElement, current: str) -> str | None:
        links = tree.xpath(
            '//nav[contains(@class, "pager")]//a[@rel="next"]/@href'
        )
        if not links:
            return None
        if len(links) != 1:
            raise ParsingException("washag: ambiguous next page")
        target = urljoin(current, links[0])
        old, new = urlsplit(current), urlsplit(target)
        old_page = parse_qs(old.query).get("page", ["0"])
        new_page = parse_qs(new.query).get("page", [])
        if (
            (new.scheme, new.netloc, new.path)
            != (old.scheme, old.netloc, old.path)
            or len(new_page) != 1
            or not new_page[0].isdigit()
            or int(new_page[0]) != int(old_page[0]) + 1
        ):
            raise ParsingException("washag: unexpected pagination target")
        return target

    @override
    async def _process_html(self) -> None:
        if self.html is None:
            raise ParsingException("washag: missing year index")
        await self._process_year(self.html, self.url)
        # In January, retain late-posted December opinions.
        if (
            not self.test_mode_enabled()
            and not self._backscraping
            and self.today.month == 1
        ):
            previous = self._year_url(self.today.year - 1)
            tree = await self._get_html_tree_by_url(previous)
            await self._process_year(tree, previous)

    async def _process_year(self, tree: HtmlElement, current: str) -> None:
        seen_pages = set()
        while True:
            signature = tuple(
                tree.xpath(
                    './/div[contains(@class, "views-field-title")]//a/@href'
                )
            )
            if signature in seen_pages:
                raise ParsingException("washag: repeated pagination content")
            seen_pages.add(signature)
            self._read_rows(tree)
            if self.test_mode_enabled():
                return
            next_url = self._next_url(tree, current)
            if not next_url:
                break
            current = next_url
            tree = await self._get_html_tree_by_url(current)

    @override
    async def _download_backwards(self, year: int) -> None:
        self._backscraping = True
        self.url = self._year_url(year)

    @staticmethod
    def cleanup_content(content: bytes) -> bytes:
        """Keep the historical opinion, not the site's navigation or footer."""
        document = html.fromstring(content)
        sections = document.xpath('//section[@id="block-atg-content"]')
        if len(sections) != 1:
            raise ValueError("washag: missing or ambiguous opinion content")
        return html.tostring(sections[0], encoding="utf-8")

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetaData:
        """Doctor supplies HTML for these HTML-only opinions.

        Use structural boundaries rather than source newlines, which disappear
        when HTML is minified. A partial or missing syllabus is not reconstructed.
        """
        if not scraped_text.strip():
            return {}
        try:
            document = html.fromstring(scraped_text)
        except (etree.ParserError, ValueError):
            return {}
        sections = document.xpath('//section[@id="block-atg-content"]')
        if len(sections) != 1:
            return {}
        section = sections[0]
        metadata: dict[str, str] = {}
        names = section.xpath(
            './/div[contains(concat(" ", normalize-space(@class), " "), " ag-name ")]'
        )
        if len(names) == 1:
            name = " ".join(names[0].text_content().split())
            if (
                name.startswith("Attorney General ")
                and name.removeprefix("Attorney General ").strip()
            ):
                metadata["judges"] = name

        # Both old Word-exported HTML and modern opinions use paragraphs, but
        # some put the title and syllabus in one paragraph separated by <br>.
        lines = []
        for paragraph in section.xpath(".//p[not(ancestor::table)]"):
            for br in paragraph.xpath(".//br"):
                br.tail = "\u2029" + (br.tail or "")
            text = paragraph.text_content()
            # Only <br>, not incidental HTML formatting, defines a line.
            # Inserted breaks are distinguished using a sentinel.
            lines.extend(
                " ".join(part.split()) for part in text.split("\u2029")
            )
            if len(lines) > 100:
                break
        lines = [line for line in lines if line and re.search(r"\w", line)]
        date_pattern = (
            r"(?:January|February|March|April|May|June|July|August|"
            r"September|October|November|December) \d{1,2}, \d{4}"
        )
        if lines and re.match(r"[A-Z][A-Z ,’'()/]+(?:—|[‐‑–-]-)", lines[0]):
            for index, line in enumerate(lines[1:20], 1):
                if re.fullmatch(date_pattern, line):
                    summary = " ".join(lines[1:index]).strip()
                    if summary:
                        metadata["summary"] = summary
                    break
        return {"OpinionCluster": metadata} if metadata else {}
