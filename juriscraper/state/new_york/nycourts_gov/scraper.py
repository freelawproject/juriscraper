"""New York Court of Appeals Docket Scraper (Court-PASS).

This module scrapes docket and filing data from the Court-PASS system
at courtpass.nycourts.gov. The site is behind a Cloudflare managed
challenge and uses ASP.NET WebForms with ViewState-driven postback
navigation, requiring a PlaywrightDriver. Every flow starts at the
Docket.aspx page.

Entry points::

    - @entry get_docket(docket_number: str)
    - @entry enumerate_dockets(argument_date?: DateRange, decision_date?: DateRange)

Both entry points converge on the same two-page pattern: the
docket-detail page provides the case title, argument date, filings
table, and attorneys; the filing-detail page (loaded via the hidden
``bttnDetails`` postback) provides decision date, issues, opinion,
citation, and the file list. Docket-detail fields are forwarded
through ``accumulated_data["deferred_docket"]`` so a single merged
``NYCourtPassDocket`` can be emitted from the filing-detail step.

Docket Lookup Flow — ``get_docket`` (emits NYCourtPassDocket)::

    1. get_docket → Docket.aspx
    2. parse_docket_page → fill APL/CTQ/JCR prefix + year + number,
       submit btnFind
    3. parse_docket_number_results → click the single matching row
       (or short-circuit straight to docket-detail if the server
       inlines it)
    4. parse_docket_detail_for_entry → forward docket-side fields
       via deferred_docket, submit bttnDetails postback
    5. parse_filing_detail_from_docket → merge filing-detail fields,
       emit NYCourtPassDocket, download files

Note, this doesn't reliably work for all dockets, consider it to only
work for undecided cases, though there are a few historical counterexamples
of this, I think they were just skipped in a manual process.


Docket Enumeration Flow — ``enumerate_dockets`` (emits NYCourtPassDocket
or NYDocketFailure)::

    1. enumerate_dockets → Docket.aspx
    2. fill_docket_search → submit the broad OR-alphabet party-name
       query so every case matches
    3. parse_docket_results → walk gvResults rows, paginate (with
       recovery for session-state races and lost context)
    4. parse_docket_detail → forward docket-side fields via
       deferred_docket, submit bttnDetails postback
    5. parse_docket_filing_detail → on caption agreement, merge
       filing-detail fields and emit NYCourtPassDocket and download
       files; on persistent mismatch, recover via a docket-number
       search (parse_docket_recovery_fill_search /
       parse_docket_recovery_select_row) or emit NYDocketFailure

Data linking:
- NYCourtPassDocket and NYCourtPassFile share a ``temp_case_id`` (UUID)
  for joining downloaded file blobs back to the docket record.
  This can also be used for sql based diagnostics to make sure the scrape
  is complete.

Design decisions:
- Separate scraper from NYCourtOfAppealsScraper (different site,
  different driver).
- Docket-detail data is forwarded to the filing-detail step so a
  single merged NYCourtPassDocket is emitted only after both pages
  have been observed and the caption check passes.
- File downloads require the current ViewState (form POST, not a
  direct URL).
- Generous timeouts for the Cloudflare challenge on first page load.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import re
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, ClassVar

from kent.common.decorators import entry, step
from kent.common.exceptions import TransientException
from kent.common.page_element import PageElement
from kent.common.param_models import DateRange
from kent.data_types import (
    BaseScraper,
    DriverRequirement,
    HttpMethod,
    HTTPRequestParams,
    ParsedData,
    Request,
    Response,
    ScraperStatus,
    SkipDeduplicationCheck,
    WaitForLoadState,
    WaitForSelector,
)
from pyrate_limiter import Duration, Rate

from .models import (
    NYCourtPassAttorney,
    NYCourtPassDocket,
    NYCourtPassDocketEntry,
    NYCourtPassFile,
    NYDocketFailure,
)
from .parsers.docket_detail import DocketDetailParser
from .parsers.docket_results import DocketResultsParser
from .parsers.filing_detail import FilingDetailParser

if TYPE_CHECKING:
    from collections.abc import Generator

    from kent.data_types import ScraperYield

logger = logging.getLogger(__name__)

COURTPASS_BASE = "https://courtpass.nycourts.gov"
DOCKET_URL = f"{COURTPASS_BASE}/Docket.aspx"

DOCKET_FORM = "//form[@id='Form2']"

DOCKET_GRID = "ctl00$cphMain$gvResults"


_Yield = NYCourtPassDocket | NYCourtPassFile | NYDocketFailure

# Search string that matches every case on the docket via "Find Any Words (OR)"
DOCKET_ENUMERATE_QUERY = (
    "a b c d e f g h i j k l m n o p q r s t u v w x y z 0 1 2 3 4 5 6 7 8 9"
)

# Cap on how many times parse_docket_filing_detail will re-walk via a
# docket-number search to recover from a bttnDetails caption mismatch.
MAX_FILING_DETAIL_RECOVERY = 2


class NYCourtPassScraper(BaseScraper[_Yield]):
    """Scraper for NY Court of Appeals dockets from Court-PASS.

    Court-PASS (courtpass.nycourts.gov) provides docket information,
    attorney details, and filing documents for cases before the
    New York Court of Appeals.

    The site is behind Cloudflare and uses ASP.NET WebForms,
    requiring PlaywrightDriver for all interactions.
    """

    # === Metadata ===
    court_ids: ClassVar[set[str]] = {"ny"}
    court_url: ClassVar[str] = COURTPASS_BASE
    data_types: ClassVar[set[str]] = {"dockets"}
    status: ClassVar[ScraperStatus] = ScraperStatus.IN_DEVELOPMENT
    version: ClassVar[str] = "2026-05-30"
    requires_auth: ClassVar[bool] = False
    driver_requirements: ClassVar[list[DriverRequirement]] = [
        DriverRequirement.JS_EVAL,
        DriverRequirement.FF_ALIKE,
        DriverRequirement.STRICTLY_SERIAL,
        DriverRequirement.CFCAP_HANDLER,
    ]

    rate_limits: ClassVar[list[Rate] | None] = [Rate(1, Duration.SECOND)]

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _parse_date_mdy(text: str) -> date | None:
        """Parse MM/DD/YYYY date string from Court-PASS pages.

        Args:
            text: Date string like '03/10/2026'

        Returns:
            Parsed date or None
        """
        text = text.strip()
        if not text:
            return None
        try:
            return datetime.strptime(text, "%m/%d/%Y").date()
        except ValueError:
            return None

    @staticmethod
    def _canonicalize_caption(text: str) -> str:
        """Normalize a case caption for cross-page substring comparison.

        The docket-detail Title cell for consolidated cases concatenates
        every party-pair with literal ``<br />`` text (the source HTML
        double-encodes the tag) or long runs of dashes/underscores as
        visual separators. The filing-detail caption shows only one
        pair. Strip those artifacts so the filing caption can be matched
        as a contiguous substring of the docket caption.
        """
        if not text:
            return ""
        text = re.sub(r"<br\s*/?>", " ", text)
        text = re.sub(r"&lt;br\s*/?&gt;", " ", text)
        text = re.sub(r"[-_]{3,}", " ", text)
        return " ".join(text.split())

    @staticmethod
    def _caption_substring_match(filing: str, docket: str) -> bool:
        """Whitespace-insensitive substring check between two captions.

        The filing-detail page wraps the case caption in three
        ``<div class="case-caption-line">`` elements (party / "v." /
        party). For captions that don't follow the implicit
        Plaintiff-v-Defendant template — e.g. ``Matter of X v Y. (App.
        Div. No. NNNNN)`` — the template injects the literal ``v.``
        between unrelated fragments, so our text-node-joining extractor
        produces ``"(App. Di v. No. NNNNN)"`` while the docket-detail
        page (which uses a single ``<dd>``) renders it as ``"(App. Div.
        No. NNNNN)"``. Strip all whitespace before the substring check
        so this one-space discrepancy doesn't trigger a false-mismatch.
        Genuine drift (e.g. different App. Div. numbers) remains
        detectable because the underlying tokens still differ.
        """
        if not filing or not docket:
            return False
        return re.sub(r"\s+", "", filing) in re.sub(r"\s+", "", docket)

    @staticmethod
    def _parse_filing_detail(
        page: PageElement,
    ) -> tuple[dict, list[NYCourtPassFile]]:
        """Run :class:`FilingDetailParser` over a filing-detail page.

        The parser owns the HTML/XPath extraction (and the unclosed
        ``<style pdffontname>`` leakage recovery that the old inline
        extractor lacked). This adapter returns:

        * ``fields`` — a dict (case_name, argument_date_str,
          decision_date_str, opinion_by, official_citation, issues,
          issue_details, no_files_for_case) with dates reshaped back to
          ``MM/DD/YYYY`` strings so the existing fallback chains
          (``deferred_docket`` / grid argument date) compose uniformly.
        * ``files`` — the parser's ``NYCourtPassFile`` rows for emission.
          ``temp_case_id`` / ``docket_number`` are not on the page; the
          caller stamps them before emitting (see
          :meth:`_stamp_files`). The file *download* buttons are a
          separate, live-form concern handled by
          :meth:`_extract_file_download_buttons`.
        """
        raw = FilingDetailParser()(page)[0].raw_data
        argument_date = raw.get("argument_date")
        decision_date = raw.get("decision_date")
        fields = {
            "case_name": raw.get("case_name"),
            "argument_date_str": (
                argument_date.strftime("%m/%d/%Y") if argument_date else None
            ),
            "decision_date_str": (
                decision_date.strftime("%m/%d/%Y") if decision_date else None
            ),
            "opinion_by": raw.get("opinion_by"),
            "official_citation": raw.get("official_citation"),
            "issues": raw.get("issues") or [],
            "issue_details": raw.get("issue_details") or [],
            "no_files_for_case": raw.get("no_files_for_case", False),
        }
        return fields, list(raw.get("files") or [])

    @staticmethod
    def _stamp_files(
        files: list[NYCourtPassFile],
        *,
        temp_case_id: str,
        docket_number: str | None,
    ) -> list[NYCourtPassFile]:
        """Attach the cross-page join keys to parser-produced file rows."""
        return [
            NYCourtPassFile(
                file_name=f.file_name,
                file_index=f.file_index,
                document_number=f.document_number,
                available=f.available,
                temp_case_id=temp_case_id,
                docket_number=docket_number or None,
            )
            for f in files
        ]

    @staticmethod
    def _extract_file_download_buttons(
        page: PageElement,
    ) -> list[dict]:
        """Map each downloadable ``gvFiles`` row to its submit-button name.

        ``FilingDetailParser`` deliberately omits the submit button's
        ``name`` attribute — it's a transient ASP.NET form field needed to
        POST a download, not data we emit. So the download mechanic reads
        it straight from the live form here. Returns one dict
        (``row_index``, ``file_name``, ``button_name``) per *available*
        file, in row order.
        """
        buttons: list[dict] = []
        file_rows = page.query_xpath(
            "//table[contains(@id, 'gvFiles')]//tr[position()>1]",
            "file rows",
            min_count=0,
        )
        for j, file_row in enumerate(file_rows):
            file_cells = file_row.query_xpath("td", "file cells", min_count=0)
            if len(file_cells) < 2:
                continue
            submit_inputs = file_row.query_xpath(
                ".//input[@type='submit']",
                "download button",
                min_count=0,
            )
            enabled = [
                b for b in submit_inputs if not b.get_attribute("disabled")
            ]
            if not enabled:
                continue
            buttons.append(
                {
                    "row_index": j,
                    "file_name": file_cells[0].text_content().strip(),
                    "button_name": enabled[0].get_attribute("name"),
                }
            )
        return buttons

    @staticmethod
    def _extract_docket_detail_fields(
        page: PageElement,
    ) -> dict:
        """Extract structured fields from a Court-PASS docket detail page.

        Thin adapter over :class:`DocketDetailParser`, which owns the
        HTML/XPath extraction. This reshapes the parser's typed output
        (a parsed ``argument_date`` and ``NYCourtPassDocketEntry`` /
        ``NYCourtPassAttorney`` instances) back into the JSON-friendly
        strings-and-dicts shape that ``deferred_docket`` and the
        NYDocketFailure builders expect — anything forwarded through
        ``accumulated_data`` has to survive a JSON round-trip between
        steps.

        Returns a dict with keys: docket_number, argument_date_str,
        case_name, docket_entries, attorneys.
        """
        raw = DocketDetailParser()(page)[0].raw_data
        argument_date = raw.get("argument_date")
        return {
            "docket_number": raw.get("docket_number"),
            "case_name": raw.get("case_name"),
            "argument_date_str": (
                argument_date.strftime("%m/%d/%Y") if argument_date else None
            ),
            "docket_entries": [
                {
                    "filing_type": e.filing_type,
                    "party": e.party,
                    "date_due": (
                        e.date_due.strftime("%m/%d/%Y") if e.date_due else ""
                    ),
                    "date_received": (
                        e.date_received.strftime("%m/%d/%Y")
                        if e.date_received
                        else ""
                    ),
                }
                for e in raw.get("docket_entries") or []
            ],
            "attorneys": [
                {
                    "party_name": a.party_name,
                    "party_role": a.party_role,
                    "firm": a.firm,
                    "attorney_name": a.attorney_name,
                    "address": a.address,
                    "phone": a.phone,
                }
                for a in raw.get("attorneys") or []
            ],
        }

    @classmethod
    def _build_docket_entries(
        cls, raw_entries: list[dict]
    ) -> list[NYCourtPassDocketEntry]:
        """Convert raw dicts to NYCourtPassDocketEntry objects."""
        return [
            NYCourtPassDocketEntry(
                filing_type=e["filing_type"],
                party=e.get("party"),
                date_due=cls._parse_date_mdy(e.get("date_due", "")),
                date_received=cls._parse_date_mdy(e.get("date_received", "")),
            )
            for e in raw_entries
        ]

    @staticmethod
    def _build_attorneys(
        raw_attorneys: list[dict],
    ) -> list[NYCourtPassAttorney]:
        """Convert raw dicts to NYCourtPassAttorney objects."""
        return [
            NYCourtPassAttorney(
                party_name=a["party_name"],
                party_role=a.get("party_role", ""),
                firm=a.get("firm"),
                attorney_name=a.get("attorney_name"),
                address=a.get("address"),
                phone=a.get("phone"),
            )
            for a in raw_attorneys
        ]

    def _emit_docket_failure(
        self,
        accumulated_data: dict,
        *,
        observed_filing_caption: str | None,
        failed_docket_search: bool,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Yield a NYDocketFailure built from ``deferred_docket`` (the
        docket-detail payload staged in parse_docket_detail) with fallback
        to top-level accumulated_data when individual fields are missing.

        Used from three sites: filing-detail caption mismatch exhausting
        recovery, recovery search returning no rows, and recovery search
        receiving a malformed docket number it cannot submit.
        """
        deferred = accumulated_data.get("deferred_docket") or {}
        yield ParsedData(
            data=NYDocketFailure(
                temp_case_id=(
                    deferred.get("temp_case_id")
                    or accumulated_data.get("temp_case_id", "")
                ),
                docket_number=(
                    deferred.get("docket_number")
                    or accumulated_data.get("docket_number")
                ),
                case_name=deferred.get("case_name") or "",
                argument_date=self._parse_date_mdy(
                    deferred.get("argument_date_str") or ""
                ),
                docket_entries=self._build_docket_entries(
                    deferred.get("docket_entries") or []
                ),
                attorneys=self._build_attorneys(
                    deferred.get("attorneys") or []
                ),
                search_page=(
                    deferred.get("search_page")
                    or accumulated_data.get("search_page")
                ),
                search_row=(
                    deferred.get("search_row")
                    if deferred.get("search_row") is not None
                    else accumulated_data.get("search_row")
                ),
                aria_case_info=(
                    deferred.get("aria_case_info")
                    or accumulated_data.get("aria_case_info")
                ),
                observed_filing_caption=observed_filing_caption,
                recovery_attempts=accumulated_data.get(
                    "filing_detail_recovery_attempts", 0
                ),
                failed_docket_search=failed_docket_search,
            )
        )

    @staticmethod
    def _date_range_to_accumulated(
        argument_date: DateRange | None,
        decision_date: DateRange | None,
    ) -> dict:
        """Serialize optional DateRange params into accumulated_data keys."""
        d: dict = {}
        if argument_date:
            d["argument_date_start"] = argument_date.start.isoformat()
            d["argument_date_end"] = argument_date.end.isoformat()
        if decision_date:
            d["decision_date_start"] = decision_date.start.isoformat()
            d["decision_date_end"] = decision_date.end.isoformat()
        return d

    @classmethod
    def _date_in_range(
        cls,
        parsed: date | None,
        range_start_str: str | None,
        range_end_str: str | None,
    ) -> bool:
        """Check whether a parsed date falls within an optional range.

        Returns True (in range / no filtering) when:
        - No range is configured (both strings are None)
        - The parsed date is None (unknown dates are never filtered)
        - The parsed date falls within [start, end]
        """
        if not range_start_str or not parsed:
            return True
        start = date.fromisoformat(range_start_str)
        end = date.fromisoformat(range_end_str) if range_end_str else start
        return start <= parsed <= end

    @staticmethod
    def _detect_actual_page(
        page: PageElement,
    ) -> int | None:
        """Detect the actual grid page from the pagination row.

        ASP.NET GridView renders the current page number as a plain
        ``<span>`` (not a hyperlink) inside the pagination row.

        Returns:
            The page number shown as current, or None if not found.
        """
        spans = page.query_xpath(
            "//table[contains(@id, 'gvResults')]"
            "//tr[last()]//td//span[not(ancestor::a)]",
            "current page indicator",
            min_count=0,
        )
        for span in spans:
            text = span.text_content().strip()
            if text.isdigit():
                return int(text)
        return None

    @staticmethod
    def _extract_visible_page_numbers(
        pagination_row: PageElement,
    ) -> list[int]:
        """Extract all page numbers available as links in the pagination row.

        Returns:
            Sorted list of page numbers that appear as ``Page$N`` links.
        """
        links = pagination_row.query_xpath(
            ".//a[contains(@href, 'Page$')]",
            "pagination page links",
            min_count=0,
        )
        pages: list[int] = []
        for link in links:
            href = link.get_attribute("href") or ""
            m = re.search(r"Page\$(\d+)", href)
            if m:
                pages.append(int(m.group(1)))
        return sorted(pages)

    # =========================================================================
    # Entry Points
    # =========================================================================

    @entry(NYCourtPassDocket)
    def get_docket(
        self,
        docket_number: str,
    ) -> Generator[Request, None, None]:
        """Look up a specific docket by APL number (e.g., 'APL-2024-00177')."""
        yield Request(
            request=HTTPRequestParams(
                method=HttpMethod.GET,
                url=DOCKET_URL,
            ),
            continuation=self.parse_docket_page,
            accumulated_data={
                "docket_number": docket_number,
                "entry_point": "get_docket",
                "coa_site_source": "docket",
            },
            deduplication_key=f"parse_docket_page:{docket_number}",
        )

    @entry(NYCourtPassDocket)
    def enumerate_dockets(
        self,
        argument_date: DateRange,
        decision_date: DateRange,
    ) -> Generator[Request, None, None]:
        """Enumerate all undecided dockets on Court-PASS.

        Searches the docket page with a broad OR query that matches
        every case, then paginates through all results, selecting
        each one to capture docket detail.

        Args:
            argument_date: If set, skip dockets whose argument date
                falls outside this range.
            decision_date: If set, skip dockets whose decision date
                falls outside this range.  Decision date is checked
                at the filing detail page since it may not be on the
                grid.
        """
        yield Request(
            request=HTTPRequestParams(
                method=HttpMethod.GET,
                url=DOCKET_URL,
            ),
            continuation=self.fill_docket_search,
            accumulated_data={
                "entry_point": "enumerate_dockets",
                "coa_site_source": "docket",
                **self._date_range_to_accumulated(
                    argument_date, decision_date
                ),
            },
            deduplication_key=f"fill_docket_search:{argument_date}:{decision_date}",
        )

    # =========================================================================
    # Docket Enumeration Flow
    # =========================================================================

    @step(
        xsd="xsds/courtpass_docket_page.xsd",
        await_list=[
            WaitForLoadState("networkidle", timeout=60000),
            WaitForSelector("#Form2", timeout=30000),
        ],
        priority=6,
    )
    def fill_docket_search(
        self,
        page: PageElement,
        response: Response,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Fill the Docket search form and submit to enumerate all dockets.

        Searches with a broad OR query that matches every case, then
        paginates through all results in ``parse_docket_results``.

        If ``target_page`` is set in accumulated_data (from a lost-context
        recovery), it is forwarded as ``page_number`` so that
        ``parse_docket_results`` will detect the page mismatch (actual=1,
        expected=N) and jump directly to the target page.
        """
        target_page = accumulated_data.get("target_page", 1)

        form = page.find_form(DOCKET_FORM, "docket search form")
        yield form.submit(
            data={
                "ctl00$cphMain$tbPartyNames": DOCKET_ENUMERATE_QUERY,
                "ctl00$cphMain$ddlFindParty": "FindOR",
            },
            submit_selector="input[name='ctl00$cphMain$btnFind']",
            continuation=self.parse_docket_results,
            accumulated_data={
                **accumulated_data,
                "page_number": target_page,
            },
        )

    @step(
        xsd="xsds/courtpass_docket_page.xsd",
        await_list=[
            WaitForLoadState("networkidle", timeout=30000),
            WaitForSelector("#Form2", timeout=15000),
        ],
        priority=5,
    )
    def parse_docket_results(
        self,
        page: PageElement,
        response: Response,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Parse docket search results and handle pagination.

        Each row has three columns: Select button, Title, Argument Date.
        Decision date is not in the grid; it's only available on the
        filing detail page. Pages have 10 results. Pagination links use
        __doPostBack.

        Uses the same page-guaranteeing strategy as ``parse_browse_results``
        to handle race conditions from concurrent workers.
        """
        expected_page = accumulated_data.get("page_number", 1)

        # --- Detect wrong page type (session-state race) ---
        # A concurrent worker may have navigated the shared session to
        # a detail page.  If we see a detail span instead of the
        # results grid, raise so the driver retries this request.
        wrong_page = page.query_xpath(
            "//span[@id='cphMain_lbDetails' or @id='cphMain_lbDetails2']",
            "detail span (wrong page)",
            min_count=0,
        )
        if wrong_page:
            raise TransientException(
                "parse_docket_results received a detail page "
                "instead of results (session-state race)"
            )

        # Pick rows by content, not by ``position()`` — the 2026-04
        # redesign separated the column header into ``<thead>``, so a
        # per-parent ``position()>1`` predicate would silently drop the
        # first ``<tbody>`` row (i.e., btnSelect_0 on every page).
        data_rows = list(
            page.query_xpath(
                "//table[contains(@id, 'gvResults')]"
                "//tr[.//input[contains(@id, 'btnSelect')]]",
                "docket data rows",
                min_count=0,
            )
        )
        pagination_rows = page.query_xpath(
            "//table[contains(@id, 'gvResults')]"
            "//tr[.//a[contains(@href, 'Page$')]]",
            "docket pagination rows",
            min_count=0,
        )
        pagination_row = pagination_rows[0] if pagination_rows else None

        # --- Detect lost search context ---
        # The server may return an empty results page (no grid at all)
        # after many pages of pagination.  When this happens there are
        # no data rows, no pagination row, and no page indicator.  If
        # we expected a page > 1, re-initiate the search and jump to
        # the target page from the fresh context.
        #
        # Guard against infinite loops: if recovery has already been
        # attempted MAX times, give up and stop pagination.
        MAX_RECOVERY_ATTEMPTS = 3
        recovery_attempts = accumulated_data.get("recovery_attempts", 0)
        if not data_rows and pagination_row is None and expected_page > 1:
            if recovery_attempts >= MAX_RECOVERY_ATTEMPTS:
                logger.warning(
                    "Docket pagination: giving up after %d recovery "
                    "attempts at page %d",
                    recovery_attempts,
                    expected_page,
                )
                return
            yield from self._reinitiate_docket_search(
                expected_page, accumulated_data
            )
            return

        # --- Validate actual page matches expected page ---
        # ASP.NET pagination links beyond the true last page silently
        # clamp: requesting Page$N+1 where N is the last page returns
        # page N again, but the rendered pagination row still shows
        # forward links for N+1, N+2, ... so the naive recovery would
        # resubmit Page$N+1 forever.  Bound the loop.
        MAX_PAGINATION_RECOVERY_ATTEMPTS = 3
        actual_page = self._detect_actual_page(page)
        if actual_page is not None and actual_page != expected_page:
            pagination_attempts = accumulated_data.get(
                "pagination_recovery_attempts", 0
            )
            if pagination_attempts >= MAX_PAGINATION_RECOVERY_ATTEMPTS:
                logger.warning(
                    "Docket pagination: giving up after %d recovery "
                    "attempts navigating from actual page %d to expected "
                    "page %d (server likely clamped past last page)",
                    pagination_attempts,
                    actual_page,
                    expected_page,
                )
                return
            yield from self._recover_docket_pagination(
                page,
                pagination_row,
                expected_page,
                actual_page,
                accumulated_data,
            )
            return

        arg_start = accumulated_data.get("argument_date_start")
        arg_end = accumulated_data.get("argument_date_end")

        # DocketResultsParser owns the per-row extraction (title,
        # argument date, aria-label, row index). The step keeps the
        # date-range filtering and per-row postback because those drive
        # navigation, not data. ``search_row`` is the parser's 0-based
        # index over the same gvResults rows, so it lines up with the
        # ``btnSelect_{i}`` submit id.
        for dv in DocketResultsParser()(page):
            row = dv.raw_data
            i = row["search_row"]
            argument_date = row.get("argument_date")

            # Skip dockets whose argument date is outside the requested
            # range. Decision date isn't in the grid; it's enforced later
            # in parse_docket_filing_detail.
            if not self._date_in_range(argument_date, arg_start, arg_end):
                continue

            argument_date_from_grid = (
                argument_date.strftime("%m/%d/%Y") if argument_date else ""
            )

            form = page.find_form(DOCKET_FORM, "docket results form")
            yield form.submit(
                data={},
                submit_selector=f"#cphMain_gvResults_btnSelect_{i}",
                continuation=self.parse_docket_detail,
                accumulated_data={
                    **accumulated_data,
                    "temp_case_id": str(uuid.uuid4()),
                    "case_short_name_from_grid": row.get("case_short_name"),
                    "argument_date_from_grid": argument_date_from_grid,
                    "search_page": expected_page,
                    "search_row": i,
                    "aria_case_info": row.get("aria_case_info"),
                },
                deduplication_key=f"docket_detail:{actual_page}:{i}:{recovery_attempts}",
            )

        # Handle pagination — find next page link
        next_page = expected_page + 1
        yield from self._navigate_to_next_docket_page(
            page,
            pagination_row,
            next_page,
            accumulated_data,
        )

    @step(
        xsd="xsds/courtpass_docket_page.xsd",
        await_list=[
            WaitForLoadState("networkidle", timeout=30000),
            WaitForSelector("#Form2", timeout=15000),
        ],
        priority=4,
    )
    def parse_docket_detail(
        self,
        page: PageElement,
        response: Response,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Parse the docket detail page and emit NYCourtPassDocket.

        Extracts APL number, argument date, filings table,
        and attorney details.  Then navigates to the filing detail
        page via the hidden ``bttnDetails`` button to collect case
        data and download files.
        """
        yield from self._process_docket_detail_page(page, accumulated_data)

    def _process_docket_detail_page(
        self,
        page: PageElement,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Shared docket-detail handling: extract docket-side fields,
        forward them via accumulated_data, and submit the bttnDetails
        postback so ``parse_docket_filing_detail`` can merge in the
        filing-detail fields and emit a single NYCourtPassDocket.

        Called from parse_docket_detail (after a normal btnSelect click)
        and from parse_docket_recovery_select_row when Court-PASS
        short-circuits a single-result docket-number search directly to
        the docket-detail page.
        """
        fields = self._extract_docket_detail_fields(page)
        # On the short-circuit response, the docket number is rendered
        # without its APL/CTQ/JCR prefix, so the extractor's regex
        # misses it. Fall back to what the original chain captured.
        docket_number = fields["docket_number"] or accumulated_data.get(
            "docket_number"
        )

        # The bttnDetails button is hidden (visibility:hidden, width:0),
        # so we can't use submit_selector (Playwright can't click it).
        # Instead, use __EVENTTARGET postback to trigger the same
        # server-side handler — kent's driver will call form.submit()
        # via JS when it sees __EVENTTARGET in field_data.
        filing_detail_data = {
            **accumulated_data,
            "docket_number": docket_number,
            "case_name_from_docket_detail": self._canonicalize_caption(
                fields["case_name"] or ""
            ),
            # Forward docket-detail fields so parse_docket_filing_detail
            # can merge them with the filing-detail fields and emit one
            # consolidated NYCourtPassDocket.
            "deferred_docket": {
                "temp_case_id": accumulated_data.get("temp_case_id", ""),
                "docket_number": docket_number,
                "case_name": fields["case_name"],
                "argument_date_str": (
                    fields["argument_date_str"]
                    or accumulated_data.get("argument_date_from_grid")
                ),
                "docket_entries": fields["docket_entries"],
                "attorneys": fields["attorneys"],
                "search_page": accumulated_data.get("search_page"),
                "search_row": accumulated_data.get("search_row"),
                "aria_case_info": accumulated_data.get("aria_case_info"),
            },
        }

        form = page.find_form(DOCKET_FORM, "docket detail form")
        yield form.submit(
            data={
                "__EVENTTARGET": "ctl00$cphMain$bttnDetails",
                "__EVENTARGUMENT": "",
            },
            continuation=self.parse_docket_filing_detail,
            accumulated_data=filing_detail_data,
            deduplication_key=f"docket_filing_detail:{docket_number}",
        )

    @step(
        xsd="xsds/courtpass_filing_detail.xsd",
        await_list=[
            WaitForLoadState("networkidle", timeout=30000),
            WaitForSelector("#cphMain_lbDetails2", timeout=15000),
        ],
        priority=3,
    )
    def parse_docket_filing_detail(
        self,
        page: PageElement,
        response: Response,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Parse the filing-detail page reached from the docket and
        emit a single merged NYCourtPassDocket.

        Merges the docket-detail fields forwarded in ``deferred_docket``
        (case_name, argument_date, docket_entries, attorneys) with the
        filing-detail fields read from this page (decision_date, issues,
        opinion_by, official_citation, files). Uses
        ``#cphMain_lbDetails2`` (not ``#cphMain_lbDetails``) and
        ``DOCKET_FORM`` for file downloads.
        """
        fields, parser_files = self._parse_filing_detail(page)

        case_name = fields["case_name"] or "Unknown"

        # The bttnDetails postback occasionally returns the filing detail
        # for a neighboring case: it reads the server's ``session.currentCase``
        # to render lbDetails2, and that state can drift from what
        # btnSelect_N set. Compare the caption from the preceding
        # docket-detail page; if it doesn't agree, recover by re-walking
        # via a docket-number search (which forces a single-row grid and
        # re-pins session state). Plain TransientException retry never
        # fixes this because it re-submits bttnDetails alone.
        #
        # Consolidated dockets concatenate multiple captions on the
        # docket-detail page but show only one on the filing-detail
        # page, so accept any contiguous substring match.
        docket_case_name = accumulated_data.get("case_name_from_docket_detail")
        filing_case_name = self._canonicalize_caption(case_name)
        if (
            docket_case_name
            and filing_case_name
            and filing_case_name != "Unknown"
            and not self._caption_substring_match(
                filing_case_name, docket_case_name
            )
        ):
            recovery_attempts = accumulated_data.get(
                "filing_detail_recovery_attempts", 0
            )
            if recovery_attempts >= MAX_FILING_DETAIL_RECOVERY:
                logger.warning(
                    "parse_docket_filing_detail: caption mismatch "
                    "persisted after %d recovery attempts for docket "
                    "%s; emitting NYDocketFailure (docket-detail "
                    "showed %r, filing-detail shows %r)",
                    recovery_attempts,
                    accumulated_data.get("docket_number"),
                    docket_case_name,
                    filing_case_name,
                )
                yield from self._emit_docket_failure(
                    accumulated_data,
                    observed_filing_caption=filing_case_name,
                    failed_docket_search=False,
                )
                return
            logger.info(
                "parse_docket_filing_detail: caption mismatch for "
                "docket %s (attempt %d); re-walking via docket-number "
                "search",
                accumulated_data.get("docket_number"),
                recovery_attempts + 1,
            )
            # Drop ``case_name_from_docket_detail`` (parse_docket_detail
            # will repopulate it on re-entry) but keep ``deferred_docket``
            # as a fallback for NYDocketFailure if the recovery's
            # docket-number search itself fails.
            recovery_ad = {
                k: v
                for k, v in accumulated_data.items()
                if k != "case_name_from_docket_detail"
            }
            recovery_ad["filing_detail_recovery_attempts"] = (
                recovery_attempts + 1
            )
            yield Request(
                request=HTTPRequestParams(
                    method=HttpMethod.GET,
                    url=DOCKET_URL,
                ),
                continuation=self.parse_docket_recovery_fill_search,
                accumulated_data=recovery_ad,
                deduplication_key=f"docket_search_fill:{recovery_attempts}",
            )
            return

        deferred = accumulated_data.get("deferred_docket") or {}

        # Fall back to the docket-grid argument date when the filing
        # detail page omits it (matches the docket-detail fallback in
        # ``_process_docket_detail_page``).
        argument_date = self._parse_date_mdy(
            fields["argument_date_str"]
            or deferred.get("argument_date_str")
            or accumulated_data.get("argument_date_from_grid")
            or ""
        )
        decision_date = self._parse_date_mdy(fields["decision_date_str"] or "")

        # --- decision_date range filtering ---
        # Decision date is now known from the filing detail page.
        # If it falls outside the requested range, skip file downloads
        # and all data emission.
        dec_start = accumulated_data.get("decision_date_start")
        dec_end = accumulated_data.get("decision_date_end")
        if not self._date_in_range(decision_date, dec_start, dec_end):
            return

        temp_case_id = deferred.get("temp_case_id") or accumulated_data.get(
            "temp_case_id", ""
        )
        docket_number = deferred.get("docket_number") or accumulated_data.get(
            "docket_number", ""
        )

        # FilingDetailParser produced the file rows (leak-aware); stamp
        # them with the cross-page join keys for emission.
        files = self._stamp_files(
            parser_files,
            temp_case_id=temp_case_id,
            docket_number=docket_number,
        )
        document_numbers_by_row = {
            f.file_index: f.document_number for f in files
        }

        # Merge docket-detail fields (from deferred) with filing-detail
        # fields (just parsed) into a single NYCourtPassDocket.
        yield ParsedData(
            data=NYCourtPassDocket(
                temp_case_id=temp_case_id,
                docket_number=docket_number or None,
                case_name=deferred.get("case_name") or case_name,
                case_short_name=(
                    accumulated_data.get("case_short_name_from_grid") or None
                ),
                argument_date=argument_date,
                decision_date=decision_date,
                issues=fields["issues"],
                issue_details=fields["issue_details"],
                opinion_by=fields["opinion_by"],
                official_citation=fields["official_citation"],
                no_files_for_case=fields["no_files_for_case"],
                docket_entries=self._build_docket_entries(
                    deferred.get("docket_entries") or []
                ),
                attorneys=self._build_attorneys(
                    deferred.get("attorneys") or []
                ),
                files=files,
                source_url=response.url,
                source_entry_point=accumulated_data.get("entry_point"),
                coa_site_source=accumulated_data.get("coa_site_source"),
                search_page=accumulated_data.get("search_page"),
                search_row=accumulated_data.get("search_row"),
                aria_case_info=accumulated_data.get("aria_case_info"),
            )
        )

        file_name_prefix = base64.b64encode(
            f"{case_name}-{argument_date}-{decision_date}".encode()
        ).decode()

        # Download available files. Button names come from the live form
        # (FilingDetailParser doesn't carry them); document_number comes
        # from the parser's file rows, keyed by row index.
        for button in self._extract_file_download_buttons(page):
            form = page.find_form(DOCKET_FORM, "docket files form")
            file_suffix = base64.b64encode(
                f"{button['file_name']}".encode()
            ).decode()
            name_sha = hashlib.sha1(
                f"{file_name_prefix}-{file_suffix}".encode()
            ).hexdigest()
            yield form.submit(
                submit_selector=f"input[name='{button['button_name']}']",
                continuation=self.handle_file_download,
                accumulated_data={
                    "temp_case_id": temp_case_id,
                    "docket_number": docket_number,
                    "file_name": button["file_name"],
                    "file_index": button["row_index"],
                    "document_number": document_numbers_by_row.get(
                        button["row_index"]
                    ),
                },
                bypass_rate_limit=True,
                priority=0,
                archive=True,
                deduplication_key=name_sha,
                request_params={"timeout": 600},
            )

    @step(
        xsd="xsds/courtpass_docket_page.xsd",
        await_list=[
            WaitForLoadState("networkidle", timeout=60000),
            WaitForSelector("#Form2", timeout=30000),
        ],
        priority=2,
    )
    def parse_docket_recovery_fill_search(
        self,
        page: PageElement,
        response: Response,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Fill the Docket search form with the target docket number.

        Recovery step for parse_docket_filing_detail caption mismatches.
        Mirrors ``parse_docket_page`` but routes the result to
        ``parse_docket_recovery_select_row`` so we rejoin the main
        enumerate_dockets chain (preserving accumulated_data such as
        ``temp_case_id`` and ``case_short_name_from_grid``).
        """
        docket_number = accumulated_data["docket_number"]
        parts = docket_number.split("-")
        if len(parts) != 3:
            logger.warning(
                "parse_docket_recovery_fill_search: cannot split "
                "docket_number %r into prefix/year/number; emitting "
                "NYDocketFailure",
                docket_number,
            )
            yield from self._emit_docket_failure(
                accumulated_data,
                observed_filing_caption=None,
                failed_docket_search=True,
            )
            return
        form = page.find_form(DOCKET_FORM, "docket form")
        yield form.submit(
            data={
                "ctl00$cphMain$ddlCaseId": parts[0],
                "ctl00$cphMain$tbCaseIdYear": parts[1],
                "ctl00$cphMain$tbCaseIdNum": parts[2],
            },
            submit_selector="input[name='ctl00$cphMain$btnFind']",
            continuation=self.parse_docket_recovery_select_row,
            accumulated_data=accumulated_data,
            deduplication_key=f"docket_search:{docket_number}:{accumulated_data['filing_detail_recovery_attempts']}",
        )

    @step(
        xsd="xsds/courtpass_docket_page.xsd",
        await_list=[
            WaitForLoadState("networkidle", timeout=30000),
            WaitForSelector("#Form2", timeout=15000),
        ],
        priority=2,
    )
    def parse_docket_recovery_select_row(
        self,
        page: PageElement,
        response: Response,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Click btnSelect_0 on a single-row docket-number search result.

        Recovery step for parse_docket_filing_detail caption mismatches.
        The docket-number search returns at most one matching row, so
        clicking btnSelect_0 unambiguously pins the server's
        ``session.currentCase`` to the case we want. Continues into the
        existing ``parse_docket_detail`` so the rest of the chain runs
        normally.

        Court-PASS may also short-circuit when the search has exactly one
        match, returning the docket-detail page directly without an
        intervening grid; we detect that via the CallDetails button on
        the docket-detail span and route into the shared
        ``_process_docket_detail_page`` helper without re-clicking.
        """
        data_rows = page.query_xpath(
            "//table[contains(@id, 'gvResults')]"
            "//tr[.//input[contains(@id, 'btnSelect')]]",
            "recovery docket data rows",
            min_count=0,
        )
        if not data_rows:
            # No grid — either we're on a "No Matching Cases" page or
            # Court-PASS short-circuited to the docket-detail page.
            # The CallDetails button is only rendered when the detail
            # span is populated, so it cleanly distinguishes the two.
            call_details_button = page.query_xpath(
                "//span[@id='cphMain_lbDetails']"
                "//button[contains(@onclick, 'CallDetails')]",
                "CallDetails button on short-circuit detail",
                min_count=0,
            )
            if call_details_button:
                logger.info(
                    "parse_docket_recovery_select_row: Court-PASS "
                    "short-circuited the docket-number search for %s "
                    "to the detail page; continuing into bttnDetails "
                    "postback directly",
                    accumulated_data.get("docket_number"),
                )
                yield from self._process_docket_detail_page(
                    page, accumulated_data
                )
                return
            logger.warning(
                "parse_docket_recovery_select_row: docket-number "
                "search returned no rows for %r; emitting "
                "NYDocketFailure(failed_docket_search=True)",
                accumulated_data.get("docket_number"),
            )
            yield from self._emit_docket_failure(
                accumulated_data,
                observed_filing_caption=None,
                failed_docket_search=True,
            )
            return
        form = page.find_form(DOCKET_FORM, "recovery docket results form")
        yield form.submit(
            data={},
            submit_selector="#cphMain_gvResults_btnSelect_0",
            continuation=self.parse_docket_detail,
            accumulated_data=accumulated_data,
            deduplication_key=f"docket_detail:{accumulated_data['docket_number']}:{accumulated_data['filing_detail_recovery_attempts']}",
        )

    @step(
        await_list=[
            # There are 3 large files that take a bit of time
            WaitForLoadState("networkidle", timeout=90000),
        ]
    )
    def handle_file_download(
        self,
        local_filepath: str | None,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Handle a downloaded file.

        Yields a NYCourtPassFile with the local path and temp_case_id
        so it can be joined with the parent NYCourtPassDocket later
        in the data pipeline.
        """
        yield ParsedData(
            data=NYCourtPassFile(
                file_name=accumulated_data.get("file_name", ""),
                file_index=accumulated_data.get("file_index"),
                document_number=accumulated_data.get("document_number"),
                local_path=local_filepath,
                available=True,
                temp_case_id=accumulated_data.get("temp_case_id"),
                docket_number=accumulated_data.get("docket_number"),
            )
        )

    # =========================================================================
    # Docket Entry Point Flow (Steps for get_docket)
    # =========================================================================

    @step(
        xsd="xsds/courtpass_docket_page.xsd",
        await_list=[
            WaitForLoadState("networkidle", timeout=60000),
            WaitForSelector("#Form2", timeout=30000),
        ],
    )
    def parse_docket_page(
        self,
        page: PageElement,
        response: Response,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Fill the Docket search form with an APL/CTQ/JCR number and submit.

        The 2026-04 redesign replaced the old single ``txtAPL`` field
        (and an even older ``txtPrefix``/``txtYear``/``txtNumber``
        variant) with a case-type dropdown + year + number trio, and
        renamed the submit button from ``bttnFind`` to ``btnFind``.
        """
        docket_number = accumulated_data["docket_number"]
        parts = docket_number.split("-")
        if len(parts) != 3:
            logger.warning(
                "parse_docket_page: cannot split docket_number %r "
                "into prefix/year/number",
                docket_number,
            )
            return
        form = page.find_form(DOCKET_FORM, "docket form")
        yield form.submit(
            data={
                "ctl00$cphMain$ddlCaseId": parts[0],
                "ctl00$cphMain$tbCaseIdYear": parts[1],
                "ctl00$cphMain$tbCaseIdNum": parts[2],
            },
            submit_selector="input[name='ctl00$cphMain$btnFind']",
            continuation=self.parse_docket_number_results,
            accumulated_data=accumulated_data,
            deduplication_key=f"docket_number_results:{docket_number}",
        )

    @step(
        xsd="xsds/courtpass_docket_page.xsd",
        await_list=[
            WaitForLoadState("networkidle", timeout=30000),
            WaitForSelector("#Form2", timeout=15000),
        ],
    )
    def parse_docket_number_results(
        self,
        page: PageElement,
        response: Response,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Parse docket search results when searching by APL number.

        Select the first (and only) matching result to view docket detail.
        The 2026-04 redesign moved row detection to a named submit button
        (``cphMain_gvResults_btnSelect_0``); the old ``OpenFiles$N``
        postback shape is now rejected by ASP.NET event validation.

        Court-PASS may also short-circuit when the search has exactly one
        match, returning the docket-detail page directly without an
        intervening grid; we detect that via the CallDetails button on
        the docket-detail span and route into the shared
        ``_process_docket_detail_for_entry`` helper without re-clicking.
        """
        data_rows = page.query_xpath(
            "//table[contains(@id, 'gvResults')]"
            "//tr[.//input[contains(@id, 'btnSelect')]]",
            "docket results data rows",
            min_count=0,
        )
        if not data_rows:
            call_details_button = page.query_xpath(
                "//span[@id='cphMain_lbDetails']"
                "//button[contains(@onclick, 'CallDetails')]",
                "CallDetails button on short-circuit detail",
                min_count=0,
            )
            if call_details_button:
                logger.info(
                    "parse_docket_number_results: Court-PASS "
                    "short-circuited the docket-number search for %s "
                    "to the detail page; continuing into bttnDetails "
                    "postback directly",
                    accumulated_data.get("docket_number"),
                )
                yield from self._process_docket_detail_for_entry(
                    page, accumulated_data
                )
                return
            logger.warning(
                "parse_docket_number_results: no rows for docket %r",
                accumulated_data.get("docket_number"),
            )
            return

        form = page.find_form(DOCKET_FORM, "docket results form")
        yield form.submit(
            data={},
            submit_selector="#cphMain_gvResults_btnSelect_0",
            continuation=self.parse_docket_detail_for_entry,
            accumulated_data=accumulated_data,
            deduplication_key=f"docket_detail_for_entry:{accumulated_data['docket_number']}",
        )

    @step(
        xsd="xsds/courtpass_docket_page.xsd",
        await_list=[
            WaitForLoadState("networkidle", timeout=30000),
            WaitForSelector("#Form2", timeout=15000),
        ],
    )
    def parse_docket_detail_for_entry(
        self,
        page: PageElement,
        response: Response,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Parse docket detail from the get_docket entry point.

        Captures the docket-side fields and forwards them via
        ``deferred_docket`` so ``parse_filing_detail_from_docket`` can
        merge them with filing-detail fields and emit one
        NYCourtPassDocket.
        """
        yield from self._process_docket_detail_for_entry(
            page, accumulated_data
        )

    def _process_docket_detail_for_entry(
        self,
        page: PageElement,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Shared docket-detail handling for the get_docket entry point.

        Called from parse_docket_detail_for_entry (after a normal
        btnSelect_0 click) and from parse_docket_number_results when
        Court-PASS short-circuits a single-result docket-number search
        directly to the docket-detail page.
        """
        fields = self._extract_docket_detail_fields(page)
        docket_number = fields["docket_number"] or accumulated_data.get(
            "docket_number"
        )

        # Generate temp_case_id to link docket + files
        temp_case_id = str(uuid.uuid4())

        # Trigger the bttnDetails postback to load the filing detail
        # into cphMain_lbDetails2. The button is ``display:none`` so we
        # can't click it via submit_selector; submit via __EVENTTARGET
        # instead, matching the enumerate_dockets flow.
        form = page.find_form(DOCKET_FORM, "docket detail form")
        yield form.submit(
            data={
                "__EVENTTARGET": "ctl00$cphMain$bttnDetails",
                "__EVENTARGUMENT": "",
            },
            continuation=self.parse_filing_detail_from_docket,
            accumulated_data={
                "temp_case_id": temp_case_id,
                "entry_point": accumulated_data.get("entry_point"),
                "coa_site_source": accumulated_data.get("coa_site_source"),
                "docket_number": docket_number,
                "deferred_docket": {
                    "temp_case_id": temp_case_id,
                    "docket_number": docket_number,
                    "case_name": fields["case_name"] or "Unknown",
                    "argument_date_str": fields["argument_date_str"],
                    "docket_entries": fields["docket_entries"],
                    "attorneys": fields["attorneys"],
                },
            },
            deduplication_key=f"filing_detail_from_docket:{docket_number}",
        )

    @step(
        xsd="xsds/courtpass_filing_detail.xsd",
        await_list=[
            WaitForLoadState("networkidle", timeout=30000),
            WaitForSelector("#cphMain_lbDetails2", timeout=15000),
        ],
    )
    def parse_filing_detail_from_docket(
        self,
        page: PageElement,
        response: Response,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Parse filing detail page when coming from the docket entry,
        merge with the deferred docket-detail fields, and emit one
        NYCourtPassDocket.
        """
        deferred = accumulated_data.get("deferred_docket") or {}
        temp_case_id = (
            deferred.get("temp_case_id")
            or accumulated_data.get("temp_case_id")
            or str(uuid.uuid4())
        )
        docket_number = deferred.get("docket_number") or accumulated_data.get(
            "docket_number"
        )

        # The bttnDetails postback populates cphMain_lbDetails2 (the
        # docket-detail section in cphMain_lbDetails stays present from
        # the prior render). FilingDetailParser reads lbDetails2 so we get
        # the filing-side fields (decision date, issues, citation, files).
        fields, parser_files = self._parse_filing_detail(page)

        case_name = (
            deferred.get("case_name") or fields["case_name"] or "Unknown"
        )
        argument_date = self._parse_date_mdy(
            fields["argument_date_str"]
            or deferred.get("argument_date_str")
            or ""
        )
        decision_date = self._parse_date_mdy(fields["decision_date_str"] or "")

        # FilingDetailParser produced the file rows (leak-aware); stamp
        # them with the cross-page join keys for emission.
        files = self._stamp_files(
            parser_files,
            temp_case_id=temp_case_id,
            docket_number=docket_number,
        )
        document_numbers_by_row = {
            f.file_index: f.document_number for f in files
        }

        yield ParsedData(
            data=NYCourtPassDocket(
                temp_case_id=temp_case_id,
                docket_number=docket_number or None,
                case_name=case_name,
                argument_date=argument_date,
                decision_date=decision_date,
                issues=fields["issues"],
                issue_details=fields["issue_details"],
                opinion_by=fields["opinion_by"],
                official_citation=fields["official_citation"],
                no_files_for_case=fields["no_files_for_case"],
                docket_entries=self._build_docket_entries(
                    deferred.get("docket_entries") or []
                ),
                attorneys=self._build_attorneys(
                    deferred.get("attorneys") or []
                ),
                files=files,
                source_url=response.url,
                source_entry_point=accumulated_data.get("entry_point"),
                coa_site_source=accumulated_data.get("coa_site_source"),
            )
        )
        file_name_prefix = base64.b64encode(
            f"{case_name}-{argument_date}-{decision_date}".encode()
        ).decode()
        # Download available files. Button names come from the live form
        # (FilingDetailParser doesn't carry them); document_number comes
        # from the parser's file rows, keyed by row index.
        for button in self._extract_file_download_buttons(page):
            file_suffix = base64.b64encode(
                f"{button['file_name']}".encode()
            ).decode()
            form = page.find_form(DOCKET_FORM, "files form")
            name_sha = hashlib.sha1(
                f"{file_name_prefix}-{file_suffix}".encode()
            ).hexdigest()
            yield form.submit(
                submit_selector=f"input[name='{button['button_name']}']",
                continuation=self.handle_file_download,
                accumulated_data={
                    "temp_case_id": temp_case_id,
                    "docket_number": docket_number,
                    "file_name": button["file_name"],
                    "file_index": button["row_index"],
                    "document_number": document_numbers_by_row.get(
                        button["row_index"]
                    ),
                },
                archive=True,
                deduplication_key=name_sha,
                request_params={"timeout": 600},
            )

    # ---- Docket pagination helpers ----

    def _reinitiate_docket_search(
        self,
        target_page: int,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Re-initiate the docket search after the server lost context.

        Yields a fresh GET to Docket.aspx with ``target_page`` in
        accumulated_data.  ``fill_docket_search`` will re-submit the
        search and set ``page_number`` to ``target_page``.  When
        ``parse_docket_results`` receives page 1 but expects page N,
        ``_recover_docket_pagination`` will step forward through the
        pagination ellipsis links until reaching the target.

        Increments ``recovery_attempts`` so the caller can detect
        infinite loops.
        """
        recovery_attempts = accumulated_data.get("recovery_attempts", 0) + 1
        logger.info(
            "Docket pagination: re-initiating search for page %d (attempt %d)",
            target_page,
            recovery_attempts,
        )
        yield Request(
            request=HTTPRequestParams(
                method=HttpMethod.GET,
                url=DOCKET_URL,
            ),
            continuation=self.fill_docket_search,
            accumulated_data={
                **accumulated_data,
                "target_page": target_page,
                "recovery_attempts": recovery_attempts,
            },
            deduplication_key=f"fill_docket_search:{recovery_attempts}",
        )

    def _recover_docket_pagination(
        self,
        page: PageElement,
        pagination_row: PageElement | None,
        expected_page: int,
        actual_page: int,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Recover when the docket results server returned the wrong page.

        If the target page is visible in the pagination row, jumps
        directly.  Otherwise steps forward via the highest visible
        page (typically the ``...`` ellipsis link) and keeps
        ``page_number`` set to the original target so the next
        ``parse_docket_results`` call will continue stepping.
        """
        if pagination_row is None:
            return

        visible = self._extract_visible_page_numbers(pagination_row)
        if not visible:
            return

        # Last page: no forward links exist beyond the current page.
        if max(visible) < actual_page:
            return

        if expected_page in visible:
            target = expected_page
        elif expected_page > actual_page:
            # Step forward via highest visible link (the "..." ellipsis)
            target = max(visible)
        else:
            target = min(visible)

        form = page.find_form(DOCKET_FORM, "docket pagination recovery")
        yield form.submit(
            data={
                "__EVENTTARGET": DOCKET_GRID,
                "__EVENTARGUMENT": f"Page${target}",
            },
            continuation=self.parse_docket_results,
            accumulated_data={
                **accumulated_data,
                "page_number": expected_page,
                "pagination_recovery_attempts": accumulated_data.get(
                    "pagination_recovery_attempts", 0
                )
                + 1,
            },
            deduplication_key=SkipDeduplicationCheck(),
        )

    def _navigate_to_next_docket_page(
        self,
        page: PageElement,
        pagination_row: PageElement | None,
        next_page: int,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Navigate to the next docket results page.

        Same strategy as ``_navigate_to_next_browse_page`` but targets
        the docket form/grid and continues to ``parse_docket_results``.
        """
        if pagination_row is None:
            return

        visible = self._extract_visible_page_numbers(pagination_row)
        if not visible:
            return

        actual_page = self._detect_actual_page(page)
        if actual_page is not None and max(visible) < actual_page:
            return

        if next_page in visible:
            target = next_page
            target_page_number = next_page
        elif any(p > next_page for p in visible):
            target = min(p for p in visible if p >= next_page)
            target_page_number = target
        elif visible:
            target = max(visible)
            target_page_number = target
        else:
            return

        form = page.find_form(DOCKET_FORM, "docket pagination")
        yield form.submit(
            data={
                "__EVENTTARGET": DOCKET_GRID,
                "__EVENTARGUMENT": f"Page${target}",
            },
            continuation=self.parse_docket_results,
            accumulated_data={
                **accumulated_data,
                "page_number": target_page_number,
                "pagination_recovery_attempts": 0,
            },
            deduplication_key=SkipDeduplicationCheck(),
        )


Site = NYCourtPassScraper
