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


Docket Enumeration Flow — ``enumerate_dockets`` (emits NYCourtPassDocket)::

    1. enumerate_dockets → Docket.aspx
    2. fill_docket_search → submit the broad OR-alphabet party-name
       query so every case matches
    3. parse_docket_results → walk gvResults rows, paginate
    4. parse_docket_detail → forward docket-side fields via
       deferred_docket, submit bttnDetails postback
    5. parse_docket_filing_detail → merge filing-detail fields, emit
       NYCourtPassDocket and download files

Data linking:
- NYCourtPassDocket and NYCourtPassFile share a ``docket_number``
  for joining downloaded file blobs back to the docket record.
  This can also be used for sql based diagnostics to make sure the scrape
  is complete.

Design decisions:
- Separate scraper from NYCourtOfAppealsScraper (different site,
  different driver).
- Docket-detail data is forwarded to the filing-detail step so a
  single merged NYCourtPassDocket is emitted only after both pages
  have been observed.
- File downloads require the current ViewState (form POST, not a
  direct URL).
- Generous timeouts for the Cloudflare challenge on first page load.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import re
from datetime import date
from typing import TYPE_CHECKING, ClassVar

from jkent.common.decorators import entry, step
from jkent.common.page_element import PageElement
from jkent.common.param_models import DateRange
from jkent.common.selector_observer import SelectorObserver
from jkent.data_types import (
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
    NYCourtPassDocket,
    NYCourtPassFile,
)
from .parsers._common import (
    _parse_date_mdy,
    page_from_text,
    repair_pdffont_leakage,
)
from .parsers.docket_detail import DocketDetailParser
from .parsers.docket_results import DocketResultsParser
from .parsers.filing_detail import FilingDetailParser

if TYPE_CHECKING:
    from collections.abc import Generator

    from jkent.data_types import ScraperYield

logger = logging.getLogger(__name__)

COURTPASS_BASE = "https://courtpass.nycourts.gov"
DOCKET_URL = f"{COURTPASS_BASE}/Docket.aspx"

DOCKET_FORM = "//form[@id='Form2']"

DOCKET_GRID = "ctl00$cphMain$gvResults"


_Yield = NYCourtPassDocket | NYCourtPassFile

# Search string that matches every case on the docket via "Find Any Words (OR)"
DOCKET_ENUMERATE_QUERY = (
    "a b c d e f g h i j k l m n o p q r s t u v w x y z 0 1 2 3 4 5 6 7 8 9"
)


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
    version: ClassVar[str] = "2026-06-17"
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
    def _parse_filing_detail(
        page: PageElement,
    ) -> tuple[dict, list[dict]]:
        """Run :class:`FilingDetailParser` over a filing-detail page.

        The parser owns the HTML/XPath extraction and assumes a clean DOM;
        the unclosed ``<style pdffontname>`` leakage is repaired upstream by
        the calling step (see ``repair_pdffont_leakage``). This adapter
        returns:

        * ``fields`` — a dict (case_name, argument_date_str,
          decision_date_str, opinion_by, official_citation, issues,
          issue_details, no_files_for_case) with dates reshaped back to
          ``MM/DD/YYYY`` strings so the existing fallback chains
          (``deferred_docket`` / grid argument date) compose uniformly.
        * ``files`` — the parser's file rows as plain dicts for emission.
          ``docket_number`` is not on the page; the caller stamps it
          before emitting (see :meth:`_stamp_files`). The file
          *download* buttons are a separate, live-form concern handled by
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
        return fields, [f.raw_data for f in raw.get("files") or []]

    @staticmethod
    def _stamp_files(
        files: list[dict],
        *,
        docket_number: str | None,
    ) -> list[dict]:
        """Attach the cross-page join key to parser-produced file rows."""
        return [{**f, "docket_number": docket_number or None} for f in files]

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
        HTML/XPath extraction. The parser returns a deferred docket whose
        ``docket_entries`` / ``attorneys`` are themselves deferred; we
        pull each one's ``raw_data`` to plain dicts so they survive the
        round-trip through ``accumulated_data["deferred_docket"]`` (dates
        are stringified by the queue's JSON encoder and re-parsed at
        ``confirm()``).

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
                e.raw_data for e in raw.get("docket_entries") or []
            ],
            "attorneys": [a.raw_data for a in raw.get("attorneys") or []],
        }

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
        """
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
                "page_number": 1,
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
        """
        expected_page = accumulated_data.get("page_number", 1)

        pagination_rows = page.query_xpath(
            "//table[contains(@id, 'gvResults')]"
            "//tr[.//a[contains(@href, 'Page$')]]",
            "docket pagination rows",
            min_count=0,
        )
        pagination_row = pagination_rows[0] if pagination_rows else None

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
                    "case_short_name_from_grid": row.get("case_short_name"),
                    "argument_date_from_grid": argument_date_from_grid,
                    "search_page": expected_page,
                    "search_row": i,
                    "aria_case_info": row.get("aria_case_info"),
                },
                deduplication_key=f"docket_detail:{expected_page}:{i}",
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

        Called from parse_docket_detail after a normal btnSelect click.
        """
        fields = self._extract_docket_detail_fields(page)
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
            # Forward docket-detail fields so parse_docket_filing_detail
            # can merge them with the filing-detail fields and emit one
            # consolidated NYCourtPassDocket.
            "deferred_docket": {
                "docket_number": docket_number,
                "case_name": fields["case_name"],
                "argument_date_str": (
                    fields["argument_date_str"]
                    or accumulated_data.get("argument_date_from_grid")
                ),
                "docket_entries": fields["docket_entries"],
                "attorneys": fields["attorneys"],
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
            deduplication_key=f"docket_filing_detail:{docket_number}:{accumulated_data.get('search_page')}-{accumulated_data.get('search_row')}",
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
        text: str,
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

        Takes the raw ``text`` (not ``page``) so the unclosed
        ``<style pdffontname>`` leakage can be repaired before lxml parses
        it — see ``repair_pdffont_leakage``; the parser and download form
        then see a clean DOM.
        """
        # We build the page ourselves (from potentially repaired text),
        # observer onto the response — this is what @step does for an
        # injected ``page`` to enable observation and debugging of selectors.
        # This scraper runs serially, _and_ the observer context is isolated
        # per async task, so we're doubly safe wrapping the whole body here.
        observer = SelectorObserver()
        response.observer = observer
        page = page_from_text(repair_pdffont_leakage(text), response.url)
        with observer:
            fields, parser_files = self._parse_filing_detail(page)

            case_name = fields["case_name"] or "Unknown"

            deferred = accumulated_data.get("deferred_docket") or {}

            # Fall back to the docket-grid argument date when the filing
            # detail page omits it (matches the docket-detail fallback in
            # ``_process_docket_detail_page``).
            argument_date = _parse_date_mdy(
                fields["argument_date_str"]
                or deferred.get("argument_date_str")
                or accumulated_data.get("argument_date_from_grid")
                or ""
            )
            decision_date = _parse_date_mdy(fields["decision_date_str"] or "")

            # --- decision_date range filtering ---
            # Decision date is now known from the filing detail page.
            # If it falls outside the requested range, skip file downloads
            # and all data emission.
            dec_start = accumulated_data.get("decision_date_start")
            dec_end = accumulated_data.get("decision_date_end")
            if not self._date_in_range(decision_date, dec_start, dec_end):
                return

            docket_number = deferred.get(
                "docket_number"
            ) or accumulated_data.get("docket_number", "")

            # FilingDetailParser produced the file rows; stamp
            # them with the cross-page join key for emission.
            files = self._stamp_files(
                parser_files,
                docket_number=docket_number,
            )
            document_numbers_by_row = {
                f["file_index"]: f["document_number"] for f in files
            }

            # Merge docket-detail fields (from deferred) with filing-detail
            # fields (just parsed) into a single NYCourtPassDocket.
            yield ParsedData(
                data=NYCourtPassDocket.raw(
                    docket_number=docket_number or None,
                    case_name=deferred.get("case_name") or case_name,
                    case_short_name=(
                        accumulated_data.get("case_short_name_from_grid")
                        or None
                    ),
                    argument_date=argument_date,
                    decision_date=decision_date,
                    issues=fields["issues"],
                    issue_details=fields["issue_details"],
                    opinion_by=fields["opinion_by"],
                    official_citation=fields["official_citation"],
                    no_files_for_case=fields["no_files_for_case"],
                    docket_entries=(deferred.get("docket_entries") or []),
                    attorneys=(deferred.get("attorneys") or []),
                    files=files,
                    source_url=response.url,
                    source_entry_point=accumulated_data.get("entry_point"),
                    search_page=accumulated_data.get("search_page"),
                    search_row=accumulated_data.get("search_row"),
                    aria_case_info=accumulated_data.get("aria_case_info"),
                )
            )

            file_name_prefix = base64.b64encode(
                f"{case_name}-{argument_date}-{decision_date}".encode()
            ).decode()

            # Download available files. Button names come from the form
            # (FilingDetailParser doesn't carry them); document_number comes
            # from the parser's file rows, keyed by row index. The form is
            # the same for every button, so read it (and the buttons) once.
            download_buttons = self._extract_file_download_buttons(page)
            form = (
                page.find_form(DOCKET_FORM, "docket files form")
                if download_buttons
                else None
            )
            for button in download_buttons:
                file_suffix = base64.b64encode(
                    f"{button['file_name']}".encode()
                ).decode()
                name_sha = hashlib.sha1(
                    f"{file_name_prefix}-{button['row_index']}-{file_suffix}".encode()
                ).hexdigest()
                yield form.submit(
                    submit_selector=(f"input[name='{button['button_name']}']"),
                    continuation=self.handle_file_download,
                    accumulated_data={
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

        Yields a NYCourtPassFile with the local path and docket_number
        so it can be joined with the parent NYCourtPassDocket later
        in the data pipeline.
        """
        yield ParsedData(
            data=NYCourtPassFile.raw(
                file_name=accumulated_data.get("file_name", ""),
                file_index=accumulated_data.get("file_index"),
                document_number=accumulated_data.get("document_number"),
                local_path=local_filepath,
                available=True,
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
                "entry_point": accumulated_data.get("entry_point"),
                "docket_number": docket_number,
                "deferred_docket": {
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
        text: str,
        response: Response,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Parse filing detail page when coming from the docket entry,
        merge with the deferred docket-detail fields, and emit one
        NYCourtPassDocket.

        Takes the raw ``text`` (not ``page``) so the unclosed
        ``<style pdffontname>`` leakage can be repaired before lxml parses
        it — see ``repair_pdffont_leakage``.
        """
        # Build the page from repaired text and wire an observer onto the
        # response so pdd telemetry works (see parse_docket_filing_detail);
        # the whole body runs under it, which is safe because each worker is
        # its own asyncio.Task (isolated context).
        observer = SelectorObserver()
        response.observer = observer
        page = page_from_text(repair_pdffont_leakage(text), response.url)
        with observer:
            deferred = accumulated_data.get("deferred_docket") or {}
            docket_number = deferred.get(
                "docket_number"
            ) or accumulated_data.get("docket_number")

            # The bttnDetails postback populates cphMain_lbDetails2 (the
            # docket-detail section in cphMain_lbDetails stays present from
            # the prior render). FilingDetailParser reads lbDetails2 so we
            # get the filing-side fields (decision date, issues, citation,
            # files).
            fields, parser_files = self._parse_filing_detail(page)

            case_name = (
                deferred.get("case_name") or fields["case_name"] or "Unknown"
            )
            argument_date = _parse_date_mdy(
                fields["argument_date_str"]
                or deferred.get("argument_date_str")
                or ""
            )
            decision_date = _parse_date_mdy(fields["decision_date_str"] or "")

            # FilingDetailParser produced the file rows; stamp
            # them with the cross-page join key for emission.
            files = self._stamp_files(
                parser_files,
                docket_number=docket_number,
            )
            document_numbers_by_row = {
                f["file_index"]: f["document_number"] for f in files
            }

            yield ParsedData(
                data=NYCourtPassDocket.raw(
                    docket_number=docket_number or None,
                    case_name=case_name,
                    argument_date=argument_date,
                    decision_date=decision_date,
                    issues=fields["issues"],
                    issue_details=fields["issue_details"],
                    opinion_by=fields["opinion_by"],
                    official_citation=fields["official_citation"],
                    no_files_for_case=fields["no_files_for_case"],
                    docket_entries=(deferred.get("docket_entries") or []),
                    attorneys=(deferred.get("attorneys") or []),
                    files=files,
                    source_url=response.url,
                    source_entry_point=accumulated_data.get("entry_point"),
                )
            )
            file_name_prefix = base64.b64encode(
                f"{case_name}-{argument_date}-{decision_date}".encode()
            ).decode()
            # Download available files. Button names come from the form
            # (FilingDetailParser doesn't carry them); document_number comes
            # from the parser's file rows, keyed by row index. The form is
            # the same for every button, so read it (and the buttons) once.
            download_buttons = self._extract_file_download_buttons(page)
            form = (
                page.find_form(DOCKET_FORM, "files form")
                if download_buttons
                else None
            )
            for button in download_buttons:
                file_suffix = base64.b64encode(
                    f"{button['file_name']}".encode()
                ).decode()
                name_sha = hashlib.sha1(
                    f"{file_name_prefix}-{file_suffix}".encode()
                ).hexdigest()
                yield form.submit(
                    submit_selector=(f"input[name='{button['button_name']}']"),
                    continuation=self.handle_file_download,
                    accumulated_data={
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

    def _navigate_to_next_docket_page(
        self,
        page: PageElement,
        pagination_row: PageElement | None,
        next_page: int,
        accumulated_data: dict,
    ) -> Generator[ScraperYield[_Yield], None, None]:
        """Navigate to the next docket results page.

        Targets the docket form/grid and continues to
        ``parse_docket_results``.
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
        elif any(p > next_page for p in visible):
            target = min(p for p in visible if p >= next_page)
        else:
            target = max(visible)

        form = page.find_form(DOCKET_FORM, "docket pagination")
        yield form.submit(
            data={
                "__EVENTTARGET": DOCKET_GRID,
                "__EVENTARGUMENT": f"Page${target}",
            },
            continuation=self.parse_docket_results,
            accumulated_data={
                **accumulated_data,
                "page_number": target,
            },
            deduplication_key=SkipDeduplicationCheck(),
        )


Site = NYCourtPassScraper
