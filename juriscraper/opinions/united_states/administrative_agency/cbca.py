"""Scraper for the Civilian Board of Contract Appeals
CourtID: cbca
Court Short Name: CBCA
Type: Published
History:
    2026-11-01: Created by abigailhaddad

Contract Disputes Act decisions from 2007 (when the Board was created) on.
Every year is on one static page, one table per year
(`AppealsDecisions<year>`), newest year first. Columns are Decision Date,
Case Number, Appellant (linked to the decision), Judge and, from 2015 on,
Type (Decision, Dismissal, Order, ...). Type is the kind of document, not
the outcome, so it is not used as `disposition`.

The regular scrape reads the current year's table (and, in January, the
previous year's, to catch late postings). The backscraper downloads the
page once and keeps the decisions dated inside the requested range.

Handling rules:
- The HTML is hand-edited. Some rows have no opening `<tr>`, or end in
  `</tr` with no `>`; lxml leaves their cells loose in the table. Rows are
  rebuilt from the cells, each starting at a cell holding only a date.
- A file linked from more than one row is emitted once. When the rows
  differ, the row whose case number and date match the filename is kept
  and the others are logged.
- Date, case number and name come from the table, not the filename.
- The Judge column is passed through as listed. "Per Curiam" is emitted as
  `per_curiam` with no judge, and "Full Board" as no judge.
- Unicode private-use characters become "-" (the one on the page stands
  for the hyphen in "CH2M-WG Idaho, LLC").
- Rows with an impossible date, no case number, other than one link, or a
  name that cleans to nothing are logged and skipped.
- Links are relative to /decisions/. A link missing its "../" is
  repointed to /files/decisions/, where the files are.

The site publishes no totals, so each table is checked against itself:
every link in the table must sit in a parsed row.
"""

import re
from datetime import date, datetime
from urllib.parse import unquote, urljoin

from typing_extensions import override

from juriscraper.AbstractSite import logger
from juriscraper.lib.utils import clean_attribute
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.cbca.gov/decisions/cda-cases.html"
    first_opinion_date = datetime(2007, 1, 1)
    date_re = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")
    docket_re = re.compile(r"^CBCA\s+\d+")
    private_use_re = re.compile("[-]")
    # The year whose table the example file was saved with
    test_year = 2026

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.base_url
        self.status = "Published"
        self.should_have_results = True
        # CBCA 2 (2007) is an .htm file
        self.expected_content_types = ["application/pdf", "text/html"]
        self._seen_urls: set[str] = set()
        # (start, end) dates to keep, both inclusive; None keeps every row
        self._date_range: tuple[date, date] | None = None
        self.make_backscrape_iterable(kwargs)

    @override
    def _process_html(self) -> None:
        if self.test_mode_enabled():
            years = [self.test_year]
        else:
            today = date.today()
            years = [today.year]
            if today.month == 1:
                years.append(today.year - 1)
        for year in years:
            self._parse_year(year)

    def _parse_year(self, year: int) -> None:
        """Parse one year's table into self.cases

        :param year: the table's year
        :return: None
        """
        if self.html is None:
            logger.error("cbca: no page to parse for %s", year)
            return
        tables = self.html.xpath(f"//table[@id='AppealsDecisions{year}']")
        if not tables:
            if year == date.today().year and date.today().month == 1:
                logger.warning("cbca: no table yet for %s", year)
            else:
                logger.error(
                    "cbca: no table with id AppealsDecisions%s on %s; the "
                    "page layout may have changed",
                    year,
                    self.url,
                )
            return
        table = tables[0]

        rows, orphans = self._group_cells(table)
        tr_rows = len(table.xpath(".//tr[td]"))
        links = len(table.xpath(".//a[@href]"))
        if orphans or len(rows) < tr_rows:
            logger.error(
                "cbca: %s table has %s rows starting with a date but %s "
                "<tr> rows, and %s cells before the first date; the layout "
                "may have changed",
                year,
                len(rows),
                tr_rows,
                orphans,
            )

        bad, other_year = [], 0
        by_url: dict[str, list[dict]] = {}
        for cells in rows:
            texts = [" ".join(c.text_content().split()) for c in cells]
            if any(self.private_use_re.search(t) for t in texts):
                logger.warning("cbca: private-use character in %r", texts)
                texts = [self.private_use_re.sub("-", t) for t in texts]
            hrefs = [
                href.strip()
                for c in cells
                for href in c.xpath(".//a/@href")
                if href.strip()
            ]
            if len(cells) not in (4, 5) or len(hrefs) != 1:
                bad.append(texts[:3])
                continue
            date_str, docket, name, judge = texts[:4]
            try:
                case_date = datetime.strptime(date_str, "%m/%d/%Y").date()
            except ValueError:
                logger.error(
                    "cbca: skipping row with impossible date: %s", texts[:3]
                )
                continue
            if not clean_attribute("case_names", name):
                logger.error(
                    "cbca: skipping row with empty name: %s", texts[:3]
                )
                continue
            if not self.docket_re.match(docket):
                bad.append(texts[:3])
                continue
            per_curiam = judge.lower() == "per curiam"
            if per_curiam or judge.lower() == "full board":
                judge = ""
            if case_date.year != year:
                other_year += 1
            url = self._make_url(hrefs[0])
            by_url.setdefault(url, []).append(
                {
                    "date": date_str,
                    "docket": docket,
                    "name": name,
                    "judge": judge,
                    "per_curiam": per_curiam,
                    "url": url,
                }
            )

        duplicates = out_of_range = 0
        for url, cases in by_url.items():
            if url in self._seen_urls:
                logger.info("cbca: %s already scraped", url)
                duplicates += len(cases)
                continue
            self._seen_urls.add(url)
            case = self._pick_row(url, cases)
            duplicates += len(cases) - 1
            if self._date_range:
                case_date = datetime.strptime(case["date"], "%m/%d/%Y").date()
                if not self._date_range[0] <= case_date <= self._date_range[1]:
                    out_of_range += 1
                    continue
            self.cases.append(case)

        if bad:
            logger.error(
                "cbca: %s of %s rows in the %s table had an unexpected "
                "shape (cell count, link or case number); skipped them. "
                "Examples: %s",
                len(bad),
                len(rows),
                year,
                bad[:3],
            )
        if other_year:
            logger.warning(
                "cbca: %s rows in the %s table are dated in another year",
                other_year,
                year,
            )
        # Every link in the table must sit in a parsed row
        links_in_rows = sum(
            len(c.xpath(".//a[@href]")) for cells in rows for c in cells
        )
        if links_in_rows != links:
            logger.error(
                "cbca: %s table has %s links but only %s are in rows that "
                "start with a date; the layout may have changed",
                year,
                links,
                links_in_rows,
            )
        logger.info(
            "cbca: %s table: %s rows, %s files, %s duplicates, %s outside "
            "the date range",
            year,
            len(rows),
            len(by_url),
            duplicates,
            out_of_range,
        )

    @staticmethod
    def _pick_row(url: str, cases: list[dict]) -> dict:
        """Choose the row that describes a file listed more than once

        Most repeats are the same row twice. But some are different
        decisions linked to the same file, so the other row's decision
        can't be reached from the page. Keep the row whose case number and
        date match the filename (filenames look like
        JUDGE_MM-DD-YY_NUMBER__APPELLANT.pdf) and report the rest.

        :param url: the document URL
        :param cases: the rows linking to it, in page order
        :return: the row to keep
        """
        if len(cases) == 1:
            return cases[0]
        unique = {tuple(sorted(c.items())) for c in cases}
        if len(unique) == 1:
            logger.info("cbca: %s listed %s times", url, len(cases))
            return cases[0]

        filename = unquote(url.rsplit("/", 1)[-1])

        def score(case: dict) -> int:
            numbers = re.findall(r"\d+", case["docket"])
            month, day, yr = case["date"].split("/")
            date_re = rf"0?{int(month)}-0?{int(day)}-(20)?{yr[-2:]}"
            return int(
                any(re.search(rf"_{n}(?!\d)", filename) for n in numbers)
            ) + int(bool(re.search(date_re, filename)))

        best = max(cases, key=score)
        others = [
            f"{c['docket']} {c['date']} {c['name']}"
            for c in cases
            if c is not best
        ]
        logger.warning(
            "cbca: %s is linked from %s different rows; kept %s %s, the "
            "others have no working link: %s",
            filename,
            len(cases),
            best["docket"],
            best["date"],
            others,
        )
        return best

    def _make_url(self, href: str) -> str:
        """Make an absolute document URL

        Links are relative to /decisions/ ("../files/decisions/..."). A
        link written "files/decisions/..." resolves to a 404 under
        /decisions/files/; the file is at /files/decisions/.

        :param href: the link as written
        :return: the absolute URL
        """
        url = urljoin(self.base_url, href)
        if "/decisions/files/decisions/" in url:
            logger.info("cbca: fixing broken relative link %s", href)
            url = url.replace(
                "/decisions/files/decisions/", "/files/decisions/"
            )
        return url

    def _group_cells(self, table) -> tuple[list[list], int]:
        """Rebuild rows from the table's cells in document order

        A new row starts at each cell holding only a date. This recovers
        rows whose `<tr>` tag is missing, which lxml leaves as loose cells.

        :param table: the year's <table> element
        :return: the rows as lists of <td> elements, and the number of
            cells found before the first date cell
        """
        rows: list[list] = []
        orphans = 0
        for cell in table.xpath(".//td"):
            text = " ".join(cell.text_content().split())
            if self.date_re.match(text):
                rows.append([cell])
            elif rows:
                rows[-1].append(cell)
            else:
                orphans += 1
        return rows, orphans

    @staticmethod
    def _parse_backscrape_date(value: str, end: bool) -> date:
        """Parse a backscrape bound: "YYYY/MM/DD", or a bare "YYYY"

        :param value: the bound as passed in
        :param end: whether this is the end of the range (a bare year then
            means December 31)
        :return: the date
        """
        if re.fullmatch(r"\d{4}", value):
            return date(int(value), 12, 31) if end else date(int(value), 1, 1)
        return datetime.strptime(value, "%Y/%m/%d").date()

    @override
    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Build the date range to backscrape, both ends inclusive

        Every year is on the same page, so the range is a single item and
        the page is downloaded once for the whole backscrape.

        :param kwargs: may contain `backscrape_start` and `backscrape_end`
            in "%Y/%m/%d" format (a bare year also works)
        :return: None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")
        start = (
            self._parse_backscrape_date(start, end=False)
            if start
            else self.first_opinion_date.date()
        )
        end = (
            self._parse_backscrape_date(end, end=True) if end else date.today()
        )
        self.back_scrape_iterable = [(start, end)]

    @override
    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Download the page once and parse every year's table in the range

        :param dates: the first and last dates to keep, both inclusive
        :return: None
        """
        start, end = dates
        logger.info("Backscraping %s to %s", start, end)
        self._date_range = (start, end)
        self.html = await self._download()
        for year in range(end.year, start.year - 1, -1):
            self._parse_year(year)
