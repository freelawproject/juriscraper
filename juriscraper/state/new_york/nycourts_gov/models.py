"""Data models for New York Court of Appeals scrapers.

These models extend ScrapedData from kent to capture
New York Court of Appeals opinion and docket data.

Supported court:
- ny: New York Court of Appeals

Data sources:
- Dockets: Court-PASS system at https://courtpass.nycourts.gov/

"""

from __future__ import annotations

from datetime import date

from kent.common.data_models import ScrapedData

# Court ID mapping
COURT_IDS = {
    "ny": "New York Court of Appeals",
}


# =========================================================================
# Court-PASS Models (courtpass.nycourts.gov)
# =========================================================================


class NYCourtPassFile(ScrapedData):
    """A file from Court-PASS filing detail page."""

    file_name: str
    """Filename as shown on the filing detail page"""

    file_index: int | None = None
    """0-based position of this file in the files table on the page"""

    document_number: int | None = None
    """1-based document number for the file, numbered from the bottom of
    the gvFiles table up. The bottom-most row is document_number=1 and the
    top-most row is document_number=len(files). Mirrors the convention used
    when attaching documents to dockets in the downstream pipeline."""

    local_path: str | None = None
    """Local filesystem path where the file was downloaded (set by driver)"""

    available: bool = True
    """False for sealed/not-available files"""

    temp_case_id: str | None = None
    """UUID linking this file to its parent NYCourtPassDocket for joining in the data pipeline"""

    docket_number: str | None = None
    """APL/CTQ/JCR number (e.g., 'APL-2024-00177') when reached via docket flow"""


class NYCourtPassDocketEntry(ScrapedData):
    """A row from the FILINGS table on the Docket detail page."""

    filing_type: str
    """Filing type (e.g., 'Appellant Brief', 'Respondent Brief')"""

    party: str | None = None
    """Party name associated with the filing"""

    date_due: date | None = None
    """Due date for the filing"""

    date_received: date | None = None
    """Date the filing was received"""


class NYCourtPassAttorney(ScrapedData):
    """Attorney info from the ATTORNEY DETAILS section of the Docket page."""

    party_name: str
    """Name of the party this attorney represents"""

    party_role: str
    """Party's role (e.g., 'Appellant', 'Respondent', 'Amicus Curiae')"""

    firm: str | None = None
    """Law firm name"""

    attorney_name: str | None = None
    """Attorney's name"""

    address: str | None = None
    """Attorney's address"""

    phone: str | None = None
    """Attorney's phone number"""


class NYCourtPassDocket(ScrapedData):
    """Docket + filing detail data from Court-PASS.

    Built by merging the docket-detail page (APL number, filings table,
    attorneys, case title) with the filing-detail page reached via
    bttnDetails (decision date, issues, opinion, citation, file list).
    Linked to NYCourtPassFile rows via ``temp_case_id``.
    """

    temp_case_id: str
    """UUID linking docket-level data to its NYCourtPassFile rows."""

    docket_number: str | None = None
    """APL number (e.g., 'APL-2024-00177')"""

    court_id: str = "ny"
    """Court identifier"""

    case_name: str = ""
    """Full case name from the docket-detail / filing-detail page."""

    case_short_name: str | None = None
    """Abbreviated case caption from the Docket.aspx grid row
    (e.g. 'People v Padilla-Zuniga (Juan)'). Captured during grid walks
    (``enumerate_dockets`` / ``net_docket``); None for direct-APL lookups."""

    argument_date: date | None = None
    """Argument date from the docket page"""

    decision_date: date | None = None
    """Date of decision (decided cases only)"""

    issues: list[str] = []
    """Issue categories (e.g., 'Environmental Conservation--...')"""

    issue_details: list[str] = []
    """Detailed issue descriptions"""

    opinion_by: str | None = None
    """Author of the opinion (decided cases only)"""

    official_citation: str | None = None
    """Official citation (decided cases only)"""

    no_files_for_case: bool = False
    """True when the filing-detail page explicitly says 'There are no
    files available for this case'."""

    docket_entries: list[NYCourtPassDocketEntry] = []
    """Filing entries from the FILINGS table"""

    attorneys: list[NYCourtPassAttorney] = []
    """Attorney details"""

    files: list[NYCourtPassFile] = []
    """Files listed on the filing-detail page (gvFiles). Each file's
    binary is emitted separately via ``handle_file_download``."""

    source_url: str | None = None
    """URL of the filing-detail page."""

    source_entry_point: str | None = None
    """Entry point used to reach this docket (e.g., 'enumerate_dockets')."""

    coa_site_source: str | None = None
    """Court-PASS surface this docket was reached through (always
    'docket' for the remaining flows)."""

    search_page: int | None = None
    """1-based page number of the Docket.aspx result grid this docket was
    found on. None when reached via a direct-APL lookup (``get_docket``)."""

    search_row: int | None = None
    """0-based row index within ``search_page`` of the Docket.aspx grid."""

    aria_case_info: str | None = None
    """Raw ``aria-label`` string from the grid's Select button."""


class NYDocketFailure(ScrapedData):
    """Record of a docket whose filing-detail page could not be confirmed.

    Emitted when ``parse_docket_filing_detail`` exhausts its
    docket-number-search recovery attempts without ever loading a
    filing-detail page whose caption agrees with the docket-detail
    caption (a Court-PASS bttnDetails session-state race).

    The docket-side data (case_name, argument_date, docket_entries,
    attorneys) is reliable because it comes from the docket-detail page,
    which we verify lines up with the row that was clicked. Only the
    filing-detail-only fields (decision_date, issues, files, etc.) are
    unavailable. Downstream consumers can use this record to retry the
    case later or to surface a known gap.
    """

    temp_case_id: str
    """UUID matching what NYCourtPassDocket / NYCourtPassCase would have used."""

    docket_number: str | None = None
    """APL/CTQ/JCR number from the docket-detail page."""

    court_id: str = "ny"
    """Court identifier."""

    case_name: str = ""
    """Case caption from the docket-detail page (reliable)."""

    argument_date: date | None = None
    """Argument date from the docket-detail page."""

    docket_entries: list[NYCourtPassDocketEntry] = []
    """Filing entries from the FILINGS table on the docket-detail page."""

    attorneys: list[NYCourtPassAttorney] = []
    """Attorney details from the docket-detail page."""

    search_page: int | None = None
    """1-based page number on the Docket.aspx grid this row was found on."""

    search_row: int | None = None
    """0-based row index within ``search_page``."""

    aria_case_info: str | None = None
    """Raw ``aria-label`` string captured from the grid's Select button."""

    failure_reason: str = "filing_detail_caption_mismatch"
    """Machine-readable failure code."""

    observed_filing_caption: str | None = None
    """Caption seen on the filing-detail page (the wrong case the server
    returned). Useful when diagnosing recurring drift patterns."""

    recovery_attempts: int = 0
    """How many docket-number-search recovery walks were attempted before
    giving up (equal to MAX_FILING_DETAIL_RECOVERY at emission time)."""

    failed_docket_search: bool = False
    """True when a recovery walk's docket-number search returned no
    matching rows (the case is genuinely not findable by docket number
    on Court-PASS, or its index entry is broken).  False means the search
    found the case but the filing-detail page still wouldn't load
    consistently."""
