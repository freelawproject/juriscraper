"""Data models for New York Court of Appeals scrapers.

These models extend ScrapedData from jkent to capture
New York Court of Appeals opinion and docket data.

Supported court:
- ny: New York Court of Appeals

Data sources:
- Dockets: Court-PASS system at https://courtpass.nycourts.gov/

"""

from __future__ import annotations

from datetime import date

from jkent.common.data_models import ScrapedData

from juriscraper.state.common_models import CleanString, HarmonizedCaseName

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
    Linked to NYCourtPassFile rows via ``docket_number``.
    """

    docket_number: str | None = None
    """APL number (e.g., 'APL-2024-00177')"""

    court: str = "ny"
    """CourtListener court ID (``ny``)."""

    case_name: HarmonizedCaseName
    """Full case name from the docket-detail / filing-detail page."""

    case_short_name: str | None = None
    """Abbreviated case caption from the Docket.aspx grid row
    (e.g. 'People v Padilla-Zuniga (Juan)'). Captured during grid walks
    (``dockets_by_bulk``); None for direct-APL lookups."""

    argument_date: date | None = None
    """Argument date from the docket page"""

    decision_date: date | None = None
    """Date of decision (decided cases only)"""

    issues: list[CleanString] = []
    """Issue categories (e.g., 'Environmental Conservation--...')"""

    issue_details: list[CleanString] = []
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
    """Entry point used to reach this docket (e.g., 'dockets_by_bulk')."""

    search_page: int | None = None
    """1-based page number of the Docket.aspx result grid this docket was
    found on. None when reached via a direct-APL lookup (``docket_by_number``)."""

    search_row: int | None = None
    """0-based row index within ``search_page`` of the Docket.aspx grid."""

    aria_case_info: str | None = None
    """Raw ``aria-label`` string from the grid's Select button."""
