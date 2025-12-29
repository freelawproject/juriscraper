"""Base class for docket scrapers.

Unlike OpinionSite which uses parallel lists, DocketSite yields structured
docket objects that contain nested data like parties, events, and documents.
"""

from datetime import date
from typing import TypedDict

from juriscraper.AbstractSite import AbstractSite
from juriscraper.lib.log_tools import make_default_logger

logger = make_default_logger()


class DocketDocument(TypedDict, total=False):
    """Base structure for a document attached to a docket entry."""

    document_url: str
    description: str
    file_size_bytes: int
    file_size_str: str


class DocketEntry(TypedDict, total=False):
    """Base structure for a docket entry.

    This is a minimal TypedDict that court-specific implementations
    can extend with additional fields.
    """

    docket_number: str
    case_name: str
    case_name_full: str
    date_filed: date
    case_type: str
    court_id: str


class DocketSite(AbstractSite):
    """Base class for docket scrapers.

    Unlike OpinionSite which uses parallel lists (case_names[], download_urls[]),
    DocketSite yields structured docket objects that contain nested data like
    parties, events, and documents.

    Subclasses should:
    1. Implement _process_html() to populate self.dockets
    2. Optionally override _check_sanity() for custom validation
    3. Implement _download_backwards() for backscraping support

    Attributes:
        dockets: List of docket entries (TypedDict objects)
        first_docket_date: Earliest date with available docket data
        days_interval: Default interval for backscraping date ranges
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # List of structured docket objects
        self.dockets: list[DocketEntry] = []

        # For backscraping - subclasses should set these
        self.first_docket_date: date | None = None
        self.days_interval: int = 7  # Default to weekly intervals

        # Expected content types for document downloads
        self.expected_content_types = ["application/pdf"]

        # Required and optional attributes for sanity checking
        # These are different from OpinionSite - we check docket structure instead
        self._req_attrs = []
        self._opt_attrs = []
        self._all_attrs = []

        # For compatibility with AbstractSite iteration
        self.case_names: list[str] = []
        self.case_dates: list[date] = []

    def __iter__(self):
        """Iterate over docket entries."""
        for docket in self.dockets:
            yield from docket

    def __getitem__(self, i):
        """Get a docket entry by index."""
        return self.dockets[i]

    def __len__(self):
        """Return number of docket entries."""
        return len(self.dockets)

    def parse(self):
        """Parse the site and populate dockets.

        Returns:
            self for method chaining
        """
        if not self.downloader_executed:
            self.html = self._download()
            self._process_html()

        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()

        # Populate case_names and case_dates for compatibility
        self._populate_compatibility_attrs()

        return self

    def _populate_compatibility_attrs(self):
        """Populate case_names and case_dates from dockets for compatibility."""
        self.case_names = []
        self.case_dates = []
        for docket in self.dockets:
            self.case_names.append(docket.get("case_name", "Unknown"))
            self.case_dates.append(docket.get("date_filed", date(1900, 1, 1)))

    def _process_html(self):
        """Process HTML and populate self.dockets.

        Subclasses must implement this method to:
        1. Parse the HTML response
        2. Populate self.dockets with DocketEntry objects
        """
        raise NotImplementedError(
            "_process_html() must be implemented by subclass"
        )

    def _check_sanity(self):
        """Validate the scraped docket data.

        Checks:
        1. All dockets have required fields (docket_number, case_name, date_filed)
        2. Dates are valid date objects
        3. No empty case names
        """
        if len(self.dockets) == 0:
            if self.should_have_results:
                logger.error(
                    f"{self.court_id}: Returned with zero dockets, but should have results."
                )
            else:
                logger.warning(f"{self.court_id}: Returned with zero dockets.")
            return

        required_fields = ["docket_number", "case_name", "date_filed"]

        for i, docket in enumerate(self.dockets):
            # Check required fields
            for field in required_fields:
                if field not in docket or not docket[field]:
                    raise ValueError(
                        f"Docket at index {i} missing required field: {field}"
                    )

            # Check date is a date object
            if not isinstance(docket.get("date_filed"), date):
                raise ValueError(
                    f"Docket at index {i} has invalid date_filed: {docket.get('date_filed')}"
                )

            # Check case_name is not empty
            if not str(docket.get("case_name", "")).strip():
                raise ValueError(f"Docket at index {i} has empty case_name")

        logger.info(
            f"{self.court_id}: Successfully found {len(self.dockets)} dockets."
        )

    def _date_sort(self):
        """Sort dockets by date_filed in descending order (newest first)."""
        if self.dockets:
            self.dockets.sort(
                key=lambda d: d.get("date_filed", date(1900, 1, 1)),
                reverse=True,
            )

    def _make_hash(self):
        """Create a unique hash for the scraped data."""
        import hashlib

        docket_numbers = [d.get("docket_number", "") for d in self.dockets]
        self.hash = hashlib.sha1(str(docket_numbers).encode()).hexdigest()

    def _download_backwards(self, d: tuple[date, date]) -> None:
        """Download dockets for a specific date range during backscraping.

        Args:
            date_range: Tuple of (start_date, end_date) to scrape

        Subclasses should implement this to:
        1. Submit search for the date range
        2. Handle pagination
        3. Populate self.dockets with results
        """
        raise NotImplementedError(
            "_download_backwards() must be implemented for backscraping"
        )
