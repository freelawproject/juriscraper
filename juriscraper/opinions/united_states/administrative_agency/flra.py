"""Scraper for the Federal Labor Relations Authority
CourtID: flra
Court Short Name: FLRA
Type: Published
History:
    2026-11-01: Created. See #1787

The Authority decisions listing is a Drupal view. Each decision takes two
table rows: the first has citation, issuance number, issuance date, case
number and (for arbitration cases) arbitrator; the second has the document
links and the parties. Recent decisions have a PDF; older ones (back to
1 FLRA, 1979) only have an HTML version.

The view accepts an issuance date range filter (inclusive on both ends),
which the backscraper uses. The unfiltered listing stops at 1,000 pages
(10,000 decisions; the site reports 10,462), so 1979-80 decisions are only
reachable through the date filter. Each page says "Displaying X - Y of N", and the
backscraper checks that it collected exactly N decisions for each range.

The site was redesigned in 2025 (old rows used `first-row` classes and
`/file/<id>/download?token=` PDF links). Most checks below log at ERROR
level so a future redesign shows up in Sentry instead of failing silently.
"""

import re
from datetime import date, datetime, timedelta
from urllib.parse import urlencode, urljoin

from lxml import html
from typing_extensions import override

from juriscraper.AbstractSite import logger
from juriscraper.lib.exceptions import InvalidDocumentError
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.flra.gov/decisions/authority-decisions"
    first_opinion_date = datetime(1979, 1, 23)
    days_interval = 90
    citation_re = re.compile(r"^(\d+) FLRA (\d+)$")
    # Party cells of pre-2008 decisions wrap the parties in the old FLRA
    # index code and year: "09:0381(45)AR - <parties> -- 1982 FLRAdec AR"
    name_prefix_re = re.compile(
        r"^:?\d+:\s?[\d-]+\([^)]*\)\s?[\w/-]*(?:\s*-)*\s*"
    )
    name_suffix_re = re.compile(
        r"(?:\s*-)*\s*(?:\d{4,5}\s*)?FLRA\s*dec\.?\s*[\w/-]*(?:\s[A-Z]{2})?"
        r"(?:(?:\s*-)*\s*v\d+\s*p[\w.]*)?(?:\s*-)*\s*$",
        re.I,
    )
    # Some cells hold only the old digest section headings, not parties
    digest_re = re.compile(
        r"^(?:FLRA CASE INFORMATION SHEET\s*|HEAD SHEET\s*)?"
        r"(?:DIGEST (?:HEADINGS|NOTES)|SUBJECT MATTER INDEX)\b"
    )

    total_re = re.compile(r"Displaying\s+\d+\s*-\s*\d+\s+of\s+(\d+)")
    # Safety cap on pages per backscrape range; ranges hold ~50 decisions
    max_pages = 100

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = f"{self.base_url}?{urlencode({'order': 'issuance_date', 'sort': 'desc'})}"
        # The unfiltered listing always shows the latest decisions, so an
        # empty result means the page layout changed
        self.should_have_results = True
        self.expected_content_types = ["application/pdf", "text/html"]
        self.make_backscrape_iterable(kwargs)

    @override
    def _process_html(self) -> None:
        self._parse_page()

    def _parse_page(self) -> int:
        """Parse one listing page into self.cases

        :return: the number of decision rows found on the page
        """
        if self.html is None:
            return 0
        # Match the exact class token; the pre-2025 layout used "first-row"
        first_rows = self.html.xpath(
            "//tbody/tr[contains(concat(' ', normalize-space(@class), ' '), ' first ')]"
        )
        bad_metadata = []
        for first_row in first_rows:
            second_rows = first_row.xpath("following-sibling::tr[1]")
            if not second_rows:
                bad_metadata.append(first_row.text_content().strip()[:80])
                continue
            links_row = second_rows[0]

            citation = self._normalize_citation(
                self._cell(first_row, "ad-citation-number")
            )
            date_str = self._cell(first_row, "issuance-date")
            # A few requests for general rulings have no case number
            # (e.g. 21 FLRA 3), so only the citation is required
            # Two dockets use non-breaking hyphens (e.g. 0\u2011AR\u20115359)
            docket = self._cell(first_row, "case-number").replace(
                "\u2011", "-"
            )
            row_ok = bool(self.citation_re.match(citation))
            if not row_ok:
                bad_metadata.append(f"{citation!r} {docket!r}")

            # Prefer the PDF, fall back to the HTML version
            pdf = links_row.xpath(".//a[normalize-space(.)='PDF']/@href")
            html_link = links_row.xpath(
                ".//a[contains(@class, 'html-link')]/@href"
            )
            if not (pdf or html_link):
                if row_ok:
                    bad_metadata.append(f"{citation!r} has no document link")
                continue
            url = urljoin(self.base_url, (pdf or html_link)[0])

            name_cells = links_row.xpath("./td[@colspan]")
            name = self._clean_name(
                " ".join(name_cells[0].text_content().split())
                if name_cells
                else ""
            )
            if name == "Decision Vacated":
                # 56 FLRA 999 links to a stub page, not a decision
                logger.warning("flra: skipping vacated stub %s", citation)
                continue
            if not name:
                # About 60 decisions (e.g. 53 FLRA 1541, 11 FLRA 692) list
                # no parties, or only digest headings
                logger.warning("flra: no parties listed for %s", citation)
                name = f"FLRA Case No. {docket}" if docket else citation

            self.cases.append(
                {
                    "name": name,
                    "url": url,
                    "date": date_str,
                    "docket": docket,
                    "citation": self._reporter_citation(citation),
                }
            )

        if bad_metadata:
            # One message per page, so a layout change makes one Sentry
            # event per run rather than one per row
            logger.error(
                "flra: %s of %s rows on %s had missing or malformed "
                "metadata; the layout may have changed. Examples: %s",
                len(bad_metadata),
                len(first_rows),
                self.url,
                bad_metadata[:3],
            )
        return len(first_rows)

    def _get_total(self) -> int | None:
        """Read N from the 'Displaying X - Y of N' summary

        :return: the total number of results, or None if not found
        """
        if self.html is None:
            return None
        text = " ".join(self.html.xpath("//text()[contains(., 'Displaying')]"))
        match = self.total_re.search(" ".join(text.split()))
        return int(match.group(1)) if match else None

    @staticmethod
    def _cell(row, field: str) -> str:
        """Get a cell's text without the mobile-only label div

        :param row: the first row of a decision
        :param field: the views-field class suffix
        :return: the cell's text
        """
        cells = row.xpath(f"./td[contains(@class, 'views-field-{field}')]")
        if not cells:
            return ""
        text = "".join(
            cells[0].xpath(
                "./text() | ./*[not(contains(@class, 'label'))]//text()"
            )
        )
        return " ".join(text.split())

    def _clean_name(self, name: str) -> str:
        """Strip the old index code and year wrapped around the parties

        :param name: the party cell's text
        :return: the parties, or "" if the cell has none
        """
        # Some cells repeat the code and year, so strip until stable
        previous = None
        while name != previous:
            previous = name
            name = self.name_prefix_re.sub("", name)
            name = self.name_suffix_re.sub("", name).strip(" -")
        if (
            self.digest_re.match(name)
            or name == "[INCOMPLETE]"
            or re.fullmatch(r"\d+ FLRA NO\.?", name)
        ):
            return ""
        return name

    def _reporter_citation(self, citation: str) -> str:
        """Use the reporters-db abbreviation, so eyecite can parse the cite

        :param citation: a validated citation such as '74 FLRA 660'
        :return: the citation as '74 F.L.R.A. 660'
        """
        match = self.citation_re.match(citation)
        if not match:
            return citation
        return f"{match.group(1)} F.L.R.A. {match.group(2)}"

    @staticmethod
    def _normalize_citation(citation: str) -> str:
        """Drop the zero padding on early volumes: '01 FLRA 75' -> '1 FLRA 75'

        :param citation: the citation as displayed
        :return: the normalized citation
        """
        return re.sub(r"^0+(\d)", r"\1", citation)

    @staticmethod
    def cleanup_content(content: bytes) -> bytes | str:
        """Strip site navigation from HTML-only decisions; pass PDFs through

        :param content: the downloaded document
        :return: the PDF bytes, or the decision's <article> HTML
        """
        if content[:5] == b"%PDF-":
            return content
        nodes = html.fromstring(content).xpath("//article")
        if not nodes:
            raise InvalidDocumentError(
                "flra: decision <article> missing from HTML page"
            )
        return html.tostring(nodes[0], encoding="unicode")

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Scrape every decision issued in a date range

        The count is checked against the site's own total. Paging through
        a range sorted only by issuance date is not stable for decisions
        that share a date: in a full backscrape, two ranges (1985-06-20 to
        1985-09-17 and 1987-03-12 to 1987-06-09) repeated 5 decisions and
        skipped 5 others. When a range comes up short, it is re-scraped one
        day at a time, which returned every decision in testing.

        :param dates: (start_date, end_date) tuple
        :return: None
        """
        # first_opinion_date is a datetime; the CLI dates are dates
        start, end = (
            d.date() if isinstance(d, datetime) else d for d in dates
        )
        logger.info("Backscraping for range %s %s", start, end)
        cases, total = await self._scrape_range(start, end)

        if total is not None and len(cases) < total and start < end:
            logger.info(
                "flra: %s of %s decisions for %s to %s; retrying by day",
                len(cases),
                total,
                start,
                end,
            )
            seen = {case["url"] for case in cases}
            day = start
            while day <= end:
                day_cases, _ = await self._scrape_range(day, day)
                for case in day_cases:
                    if case["url"] not in seen:
                        seen.add(case["url"])
                        cases.append(case)
                day += timedelta(days=1)

        self.cases.extend(cases)
        if total is None:
            if cases:
                logger.error(
                    "flra: no 'Displaying X - Y of N' summary for %s to %s; "
                    "can't confirm the range is complete",
                    start,
                    end,
                )
        elif len(cases) != total:
            logger.error(
                "flra: collected %s decisions for %s to %s but the site "
                "reports %s",
                len(cases),
                start,
                end,
                total,
            )

    async def _scrape_range(
        self, start: date, end: date
    ) -> tuple[list[dict], int | None]:
        """Page through one date-filtered listing

        Pages are requested until one comes back empty, rather than
        following the pager links, so a pager redesign can't silently
        truncate the backscrape. Decisions outside the range (a sign the
        date filter stopped working) are dropped and reported, and each
        decision is kept once.

        :param start: first issuance date, inclusive
        :param end: last issuance date, inclusive
        :return: the unique in-range cases, and the site's reported total
        """
        params = {
            "issuance_date_op": "between",
            "issuance_date[min]": start.strftime("%Y-%m-%d"),
            "issuance_date[max]": end.strftime("%Y-%m-%d"),
            "order": "issuance_date",
            "sort": "desc",
        }
        before = len(self.cases)
        total = None
        for page in range(self.max_pages):
            self.url = f"{self.base_url}?{urlencode({**params, 'page': page})}"
            self.html = await self._download()
            if total is None:
                total = self._get_total()
            if not self._parse_page():
                break
        else:
            logger.error(
                "flra: hit %s pages for %s to %s; stopping",
                self.max_pages,
                start,
                end,
            )
        new_cases = self.cases[before:]
        del self.cases[before:]

        in_range, seen_urls, out_of_range = [], set(), 0
        for case in new_cases:
            case_date = convert_date_string(case["date"])
            if not (case_date and start <= case_date <= end):
                out_of_range += 1
                continue
            if case["url"] in seen_urls:
                logger.warning("flra: %s listed twice", case["url"])
                continue
            seen_urls.add(case["url"])
            in_range.append(case)
        if out_of_range:
            logger.error(
                "flra: %s of %s decisions fell outside %s to %s; the date "
                "filter may have changed. Dropped them.",
                out_of_range,
                len(new_cases),
                start,
                end,
            )
        return in_range, total
