"""Scraper for U.S. Merit Systems Protection Board
CourtID: mspb
Court Short Name: MSPB
Author: Jon Andersen
Reviewer: mlr
Date created: 1 Sep 2014
Type: Precedential
History:
    2026-11-01: Read the manifest MSPB's own listing page uses instead of
        the stale _Table.json; add a backscraper.

MSPB publishes its decisions as JSON "manifests" that its own search and
listing pages load. Nothing else links to them, so their names come from
www.mspb.gov/decisions/PrecedentialDecSearch.html,
NonPrecedentialDecSearch.html, precdec.htm and nonprecdec.htm:

- ``PrecedentialDecisions_Manifest.json``: loaded by precdec.htm.
  Metadata only, 2022-03-24 onward. Used for the daily scrape.
- ``PrecedentialDecisions_Manifest_updMar2025.json``: loaded by the
  search page for a metadata search. Every precedential decision back
  to 1979; in Nov. 2026 it had not been updated since 2026-09-02.
- ``PrecedentialDecisions_Manifest_Table.json``: what this scraper used
  to read. 2022 onward; also last updated 2026-09-02.
- ``SEARCH_MANIFESTS/PrecedentialDecisions_Manifest_<range>.json``: the
  same decisions with full text, in five-year files, for full-text
  search. Not used: in Nov. 2026 they held no decision with a working
  PDF link that the files above lack, and together they are ~200 MB.

Each row has a FILE_NAME relative to the decisions folder, an
ISSUED_DATE (usually YYYY/MM/DD, sometimes MM/DD/YYYY), the docket
number, appellant name and agency. Rows are keyed by FILE_NAME: a
manifest can repeat a row, and the manifests overlap.

The backscraper reads every manifest in ``backscrape_manifests`` in one
pass, merges them by file name and keeps the rows in the requested date
range. Problems that would otherwise drop decisions silently (a missing
file name, an unparseable or impossible date, a manifest of the wrong
type) are logged at ERROR level or raised.
"""

import asyncio
import json
import re
from datetime import date, datetime
from urllib.parse import quote

from typing_extensions import override

from juriscraper.AbstractSite import logger
from juriscraper.lib.exceptions import InvalidDocumentError
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base = "https://www.mspb.gov/decisions/precedential/"
    current_manifest = "PrecedentialDecisions_Manifest.json"
    backscrape_manifests = [
        "PrecedentialDecisions_Manifest_updMar2025.json",
        "PrecedentialDecisions_Manifest.json",
        "PrecedentialDecisions_Manifest_Table.json",
    ]
    document_type = "PRECEDENTIAL"
    # The Board's first decisions were issued in 1979
    first_opinion_date = date(1979, 1, 1)
    days_interval = 366
    # Seconds between manifest downloads in a backscrape
    request_pause = 1.5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = f"{self.base}{self.current_manifest}"
        self.should_have_results = True
        self.expected_content_types = ["application/pdf"]
        self.seen_files: set[str] = set()
        self.make_backscrape_iterable(kwargs)

    @override
    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Backscrape the whole requested range in one pass

        Every manifest spans many years, so splitting the range would
        download the same files once per chunk.

        :param kwargs: may hold backscrape_start and backscrape_end
        :return: None; sets self.back_scrape_iterable
        """
        super().make_backscrape_iterable(kwargs)
        if self.back_scrape_iterable:
            self.back_scrape_iterable = [
                (
                    self.back_scrape_iterable[0][0],
                    self.back_scrape_iterable[-1][-1],
                )
            ]

    @override
    def _process_html(self) -> None:
        if self.test_mode_enabled():
            # Example files end in .html, so the mock response isn't
            # decoded as JSON
            with open(self.mock_url) as file:
                self.html = json.load(file)
        self._parse_manifest(self.html, self.url)

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Read every manifest and keep decisions issued in a date range

        :param dates: (start, end) dates, inclusive
        :return: None
        """
        start, end = (
            d.date() if isinstance(d, datetime) else d for d in dates
        )
        for i, name in enumerate(self.backscrape_manifests):
            if i:
                # Be polite between the large manifest downloads
                await asyncio.sleep(self.request_pause)
            self.url = f"{self.base}{name}"
            logger.info("mspb: backscraping %s for %s to %s", name, start, end)
            manifest = await self._download()
            before = len(self.cases)
            self._parse_manifest(manifest, self.url, start, end)
            logger.info(
                "mspb: %s added %s decisions not in earlier manifests",
                name,
                len(self.cases) - before,
            )

    def _parse_manifest(
        self,
        manifest,
        url: str,
        start: date | None = None,
        end: date | None = None,
    ) -> None:
        """Add a manifest's rows to self.cases

        :param manifest: the decoded JSON
        :param url: where it came from, for log messages
        :param start: if given, skip decisions issued before this date
        :param end: if given, skip decisions issued after this date
        :return: None
        """
        if not isinstance(manifest, dict) or "data" not in manifest:
            raise InvalidDocumentError(
                f"mspb: {url} is not a decision manifest (no 'data' key)"
            )
        if manifest.get("DOCUMENT_TYPE") != self.document_type:
            raise InvalidDocumentError(
                f"mspb: {url} has DOCUMENT_TYPE "
                f"{manifest.get('DOCUMENT_TYPE')!r}, expected "
                f"{self.document_type!r}"
            )

        no_file, bad_date = [], []
        for row in manifest["data"]:
            file_name = (row.get("FILE_NAME") or "").strip()
            if not file_name:
                no_file.append(
                    f"{row.get('DOCKET_NBR')} {row.get('ISSUED_DATE')}"
                )
                continue
            key = file_name.lower()
            if key in self.seen_files:
                continue

            issued = self._parse_date(row.get("ISSUED_DATE") or "")
            if issued is None:
                bad_date.append(f"{file_name} {row.get('ISSUED_DATE')!r}")
                continue
            if (start and issued < start) or (end and issued > end):
                continue
            self.seen_files.add(key)

            case = {
                "name": self._make_name(row),
                "url": f"{self.base}{quote(file_name)}",
                "docket": (row.get("DOCKET_NBR") or "").strip(),
                "date": issued.isoformat(),
            }
            # Every case needs the same keys: the optional getters only
            # look at the first case. Decision numbers ("2006 MSPB 10")
            # start in 2000; older decisions only have an M.S.P.R. cite.
            citation = (row.get("DECISION_NUMBER") or "").strip()
            reporter = (row.get("LEGAL_CITATION") or "").strip()
            case["citation"] = citation or reporter
            case["parallel_citation"] = reporter if citation else ""
            self.cases.append(case)

        # One message per manifest, so a format change makes one Sentry
        # event per run rather than one per row
        if no_file:
            logger.error(
                "mspb: %s rows in %s have no FILE_NAME and were skipped: %s",
                len(no_file),
                url,
                no_file[:5],
            )
        if bad_date:
            logger.error(
                "mspb: %s rows in %s have a missing or impossible "
                "ISSUED_DATE and were skipped: %s",
                len(bad_date),
                url,
                bad_date[:5],
            )

    def _parse_date(self, value: str) -> date | None:
        """Parse an ISSUED_DATE

        :param value: 'YYYY/MM/DD' or 'MM/DD/YYYY'
        :return: the date, or None if it is unparseable or outside
            1979 to today (two 1980s rows read 0891/01/01 and 1087/11/27)
        """
        value = value.strip()
        for fmt in ("%Y/%m/%d", "%m/%d/%Y", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(value, fmt).date()
            except ValueError:
                continue
            if self.first_opinion_date <= parsed <= date.today():
                return parsed
            return None
        return None

    @staticmethod
    def _make_name(row: dict) -> str:
        """Build 'First Last v. Agency', falling back to DOCNAME

        :param row: a manifest row
        :return: the case name
        """
        first = row.get("APL_FIRST_NAME") or ""
        last = row.get("APL_LAST_NAME") or ""
        appellant = " ".join(f"{first} {last}".split())
        agency = " ".join((row.get("AGENCY") or "").split())
        if appellant and agency:
            return f"{appellant} v. {agency}"
        if appellant:
            return appellant
        # e.g. 'Smith, John  - DC-0752-10-0001-I-1 - Final Order'
        docname = re.split(r"\s+-\s+", row.get("DOCNAME") or "")[0]
        return " ".join(docname.split()) or (row.get("DOCKET_NBR") or "")
