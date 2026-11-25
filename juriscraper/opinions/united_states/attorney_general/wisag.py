"""Scraper for the Wisconsin Attorney General
CourtID: wisag
Court Short Name: Wisconsin Attorney General
History:
 - 2026-11-26: Created
"""

import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from lxml import html
from lxml.html import HtmlElement
from typing_extensions import override

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    recent_url = "https://docs.legis.wisconsin.gov/misc/oag/recent"
    # Lists 1995 to 1999 opinions, followed by volumes 71 to 81 (1982 to
    # 1994). Those volumes are in CourtListener already, from the Columbia
    # archive, without docket numbers, so they are not scraped
    archival_url = "https://docs.legis.wisconsin.gov/misc/oag/archival"
    first_opinion_date = date(1995, 1, 1)
    # The listings have no dates, each opinion page has to be downloaded.
    # Few opinions are issued each year, so only the most recent are checked
    regular_scrape_size = 5

    # "oag1-24": opinion number and last 2 digits of the year
    number_regex = re.compile(r"^oag(?P<number>\d+)-(?P<year>\d{2})$")
    # Dates are searched for with all the whitespace removed, since the HTML
    # has stray spaces in them: "February 1 4 , 2008" (OAG 1-08) or
    # "January 28 , 20 20" (OAG 1-20)
    date_regex = re.compile(
        r"(?P<month>January|February|March|April|May|June|July|August"
        r"|September|October|November|December)"
        r"(?P<day>\d{1,2}),(?P<year>\d{4})"
    )
    # Only the letterhead is searched for the date, so that dates cited in
    # the opinion are not picked up
    letterhead_size = 1000
    # "Josh Kaul Attorney General" or, on two lines, "J.B. VAN HOLLEN" and
    # "ATTORNEY GENERAL". The deputy is listed below the Attorney General
    attorney_general_regex = re.compile(
        r"^(?P<name>.*?)\s*Attorney General$", re.I
    )
    name_regex = re.compile(r"^[A-Z][\w.'-]*(?: [A-Z][\w.'-]*){1,4}$")
    # Marks line breaks while the text is extracted
    line_break = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.recent_url
        self.status = "Published"
        self.should_have_results = True
        # 1995 to 1999 opinions have no PDF, the HTML page is downloaded
        self.expected_content_types = ["application/pdf", "text/html"]
        self.make_backscrape_iterable(kwargs)

    @override
    async def _process_html(self) -> None:
        """Get the most recent opinions of the listing page"""
        if self.html is None:
            return
        entries = self._get_listing_entries(self.html)
        for entry in entries[: self.regular_scrape_size]:
            await self._add_opinion(entry)

    def _get_listing_entries(self, listing: HtmlElement) -> list[dict]:
        """Parse a listing page, newest opinion first

        :param listing: the "recent" or "archival" listing page
        :return: a dict per opinion, with its docket number, year, page URL
            and download URL
        """
        entries = []
        for item in listing.xpath("//ul[@class='docLinks']/li"):
            link = item.xpath(".//a")[0]
            match = self.number_regex.match(link.text_content().strip())
            if not match:
                # volumes of the archival page, such as "vol81-1"
                continue
            year = int(match.group("year"))
            year += 1900 if year >= 95 else 2000
            page_url = link.get("href")
            # The opinions issued before 2000 don't have a PDF
            pdf_url = item.xpath(".//span[@class='pdfLink']/a/@href")
            entries.append(
                {
                    "docket": f"OAG {match.group('number')}-"
                    f"{match.group('year')}",
                    "year": year,
                    "page_url": page_url,
                    "url": pdf_url[0] if pdf_url else page_url,
                }
            )
        return entries

    async def _add_opinion(self, entry: dict) -> None:
        """Download the opinion page and add the opinion to the cases

        :param entry: a dict from `_get_listing_entries`
        :return: None
        """
        docket = entry["docket"]
        page = await self._get_opinion_page(entry["page_url"])
        self.cases.append(
            {
                "docket": docket,
                "name": f"Wisconsin Attorney General Opinion {docket}",
                "url": entry["url"],
                **self._parse_opinion_page(page, docket, entry["year"]),
            }
        )

    async def _get_opinion_page(self, url: str) -> HtmlElement | None:
        """Download an opinion page, which starts with the letterhead

        :param url: the opinion's link on the listing page, which redirects
            to the opinion page
        :return: the opinion page, or None if it couldn't be downloaded
        """
        if self.test_mode_enabled():
            # Example opinion pages are named after the link on the listing
            assert self.mock_url is not None
            name = Path(urlparse(url).path).name
            self.mock_url = str(
                Path(self.mock_url).with_name(f"wisag_subexample_{name}.html")
            )
            await self._request_url_mock(url)
            return self._return_response_text_object()

        try:
            return await self._get_html_tree_by_url(url)
        except httpx.HTTPError as e:
            logger.warning("wisag: could not get %s: %s", url, e)
            return None

    def _parse_opinion_page(
        self, page: HtmlElement | None, docket: str, year: int
    ) -> dict:
        """Get the date, the Attorney General and the summary of an opinion

        Some opinions don't have a date, or have a wrong one: OAG 1-11 is
        dated June 10, 2025 on the source. They get an approximate date in the
        middle of the year of their number. Some opinions are issued the year
        after the one in their number, so that year is accepted too

        :param page: the opinion page
        :param docket: the opinion number, for logging
        :param year: the year in the opinion number
        :return: a dict with the date, judge and summary of the opinion
        """
        lines = self._get_lines(page) if page is not None else []
        opinion_date = self._get_date(lines)
        approximate = False
        if opinion_date is None or not (year <= opinion_date.year <= year + 1):
            logger.warning(
                "wisag: no valid date for %s (found %s), using an "
                "approximate date",
                docket,
                opinion_date,
            )
            opinion_date = date(year, 7, 1)
            approximate = True

        text = " ".join(lines)
        # Older opinions end with a summary. Pages show up to 60 paragraphs,
        # so it is missing from those of the longer opinions
        _, caption, summary = text.rpartition("CAPTION:")

        return {
            "date": opinion_date.isoformat(),
            "date_filed_is_approximate": approximate,
            "judge": self._get_attorney_general(lines),
            "summary": summary.strip() if caption else "",
        }

    def _get_lines(self, page: HtmlElement) -> list[str]:
        """Get the lines of text of the opinion

        :param page: the opinion page
        :return: the non empty lines of the opinion, with normalized spaces
        """
        lines = []
        for paragraph in page.xpath("//div[@id='document']/div[@data-path]"):
            for br in paragraph.iter("br"):
                br.tail = self.line_break + (br.tail or "")
            text = paragraph.text_content().split(self.line_break)
            lines.extend(
                normalized
                for line in text
                if (normalized := " ".join(line.split()))
            )
        return lines

    def _get_date(self, lines: list[str]) -> date | None:
        """Get the date from the letterhead of the opinion

        :param lines: the lines of the opinion
        :return: the date, or None if not found
        """
        letterhead = lines[: self._get_salutation_index(lines)]
        text = " ".join(letterhead)[: self.letterhead_size]
        match = self.date_regex.search(re.sub(r"\s", "", text))
        if not match:
            return None
        try:
            return datetime.strptime(
                " ".join(match.groups()), "%B %d %Y"
            ).date()
        except ValueError:
            return None

    @staticmethod
    def _get_salutation_index(lines: list[str]) -> int:
        """Find the salutation, which follows the letterhead

        :param lines: the lines of the opinion
        :return: the index of the salutation, or the number of lines
        """
        for i, line in enumerate(lines):
            # "Dear Governor Evers:", or "De ar Governor Evers :" (OAG 4-20)
            if re.sub(r"\s", "", line).startswith("Dear"):
                return i
        return len(lines)

    def _get_attorney_general(self, lines: list[str]) -> str:
        """Get the Attorney General's name from the letterhead, or from the
        signature, since 1995 to 1999 opinions don't have a letterhead

        :param lines: the lines of the opinion
        :return: the name of the Attorney General, or an empty string
        """
        candidates = lines[: min(self._get_salutation_index(lines), 20)]
        for i, line in enumerate(lines):
            if line.startswith("Sincerely"):
                # "Sincerely,", "James E. Doyle", "Attorney General"
                signature = line.removeprefix("Sincerely").lstrip(", ")
                candidates += ["", signature, *lines[i + 1 : i + 3]]
                break

        for i, line in enumerate(candidates):
            if not (match := self.attorney_general_regex.match(line)):
                continue
            name = match.group("name") or (candidates[i - 1] if i else "")
            if self.name_regex.match(name) and "Deputy" not in name:
                return titlecase(name) if name.isupper() else name
        return ""

    @override
    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Get the opinions whose number is from a year in the range

        :param dates: (start, end) tuple; only the years are used
        :return: None
        """
        start, end = dates
        logger.info("Backscraping for years %s to %s", start.year, end.year)
        urls = []
        if end.year >= 2000:
            urls.append(self.recent_url)
        if start.year < 2000:
            urls.append(self.archival_url)

        for url in urls:
            self.url = url
            self.html = await self._download()
            for entry in self._get_listing_entries(self.html):
                if start.year <= entry["year"] <= end.year:
                    await self._add_opinion(entry)

    @override
    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Make a single (start, end) tuple

        The listings can't be filtered, so they are read once and the
        opinions are filtered by the year in their number

        :param kwargs: may contain `backscrape_start` and `backscrape_end`
            in "%Y/%m/%d" format. Defaults to all the opinions since 1995
        :return: None; sets self.back_scrape_iterable in place
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")
        start = (
            datetime.strptime(start, "%Y/%m/%d").date()
            if start
            else self.first_opinion_date
        )
        end = (
            datetime.strptime(end, "%Y/%m/%d").date() if end else date.today()
        )
        self.back_scrape_iterable = [(start, end)]

    @staticmethod
    def cleanup_content(content: bytes) -> bytes:
        """Keep only the opinion from the HTML pages of 1995 to 1999
        opinions, dropping the site's menus. PDFs are returned unchanged

        :param content: the downloaded opinion
        :return: the cleaned content
        """
        if content.startswith(b"%PDF"):
            return content
        # The pages don't declare their encoding, only the HTTP headers do
        tree = html.fromstring(
            content, parser=html.HTMLParser(encoding="utf-8")
        )
        documents = tree.xpath("//div[@id='document']")
        if not documents:
            return content
        document = documents[0]
        # "Up" and "Down" links, for scrolling through the archive
        for navigation in document.xpath("./div[not(@data-path)]"):
            navigation.drop_tree()
        return html.tostring(document, encoding="utf-8")
