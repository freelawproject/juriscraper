"""
Scraper for Texas appellate court dockets from TAMES.

This scraper searches the Texas Courts case search system (TAMES) and
retrieves docket information for cases from all Texas appellate courts:
- Supreme Court (cossup)
- Court of Criminal Appeals (coscca)
- Courts of Appeals (coa01 through coa15)

Website: https://search.txcourts.gov/CaseSearch.aspx
"""

import re
from collections.abc import Generator
from datetime import date, timedelta
from typing import Final, Optional
from urllib.parse import parse_qs, urlparse

from lxml import etree, html

from juriscraper.lib.log_tools import make_default_logger
from juriscraper.state.BaseStateScraper import (
    BaseStateScraper,
    ScraperRequestManager,
)
from juriscraper.state.texas.common import CourtID, TexasCommonData
from juriscraper.state.texas.court_of_appeals import TexasCourtOfAppealsScraper
from juriscraper.state.texas.court_of_criminal_appeals import (
    TexasCourtOfCriminalAppealsScraper,
)
from juriscraper.state.texas.supreme_court import TexasSupremeCourtScraper

logger = make_default_logger()

# Court type identifiers used in TAMES URLs
COURT_TYPE_SUPREME = "cossup"
COURT_TYPE_CRIMINAL_APPEALS = "coscca"
COURT_TYPE_APPEALS_PREFIX = "coa"  # coa01, coa02, etc.

# All Texas appellate court identifiers
ALL_COURTS = [
    COURT_TYPE_SUPREME,
    COURT_TYPE_CRIMINAL_APPEALS,
    "coa01",
    "coa02",
    "coa03",
    "coa04",
    "coa05",
    "coa06",
    "coa07",
    "coa08",
    "coa09",
    "coa10",
    "coa11",
    "coa12",
    "coa13",
    "coa14",
    "coa15",
]

COURT_CHECKBOX_MAPPING: dict[str,str] = {
    "texas_cossup": "ctl00$ContentPlaceHolder1$chkListCourts$0",
    "texas_coscca": "ctl00$ContentPlaceHolder1$chkListCourts$1",
    "texas_coa01": "ctl00$ContentPlaceHolder1$chkListCourts$2",
    "texas_coa02": "ctl00$ContentPlaceHolder1$chkListCourts$3",
    "texas_coa03": "ctl00$ContentPlaceHolder1$chkListCourts$4",
    "texas_coa04": "ctl00$ContentPlaceHolder1$chkListCourts$5",
    "texas_coa05": "ctl00$ContentPlaceHolder1$chkListCourts$6",
    "texas_coa06": "ctl00$ContentPlaceHolder1$chkListCourts$7",
    "texas_coa07": "ctl00$ContentPlaceHolder1$chkListCourts$8",
    "texas_coa08": "ctl00$ContentPlaceHolder1$chkListCourts$9",
    "texas_coa09": "ctl00$ContentPlaceHolder1$chkListCourts$10",
    "texas_coa10": "ctl00$ContentPlaceHolder1$chkListCourts$11",
    "texas_coa11": "ctl00$ContentPlaceHolder1$chkListCourts$12",
    "texas_coa12": "ctl00$ContentPlaceHolder1$chkListCourts$13",
    "texas_coa13": "ctl00$ContentPlaceHolder1$chkListCourts$14",
    "texas_coa14": "ctl00$ContentPlaceHolder1$chkListCourts$15",
    "texas_coa15": "ctl00$ContentPlaceHolder1$chkListCourts$16",
}


class TAMESScraper(BaseStateScraper[TexasCommonData]):
    """Scraper for Texas appellate court dockets from TAMES.

    Searches the Texas Courts case search system by date range and
    retrieves full docket information for each case.

    Attributes:
        BASE_URL: Base URL for TAMES
        SEARCH_URL: URL for the case search form
        ALL_COURTS_CHECKBOX: Form field name for selecting all courts
    """

    BASE_URL = "https://search.txcourts.gov"
    SEARCH_URL = f"{BASE_URL}/CaseSearch.aspx"

    # Default days interval for backscraping (weekly to stay under 1000-result limit)
    DEFAULT_DAYS_INTERVAL = 7

    # Oldest (inaccurately) dated records in TAMES
    FIRST_RECORD_DATE = date(1900, 1, 1)

    # Additional headers for ASP.NET form submission
    ADDITIONAL_HEADERS: Final[dict[str, str]] = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    COURT_IDS: Final[list[str]] = [c.value for c in CourtID]

    def __init__(
        self,
        request_manager: Optional[ScraperRequestManager] = None,
        days_interval: int = DEFAULT_DAYS_INTERVAL,
        **kwargs,
    ) -> None:
        """Initialize the TAMES scraper.

        Args:
            request_manager: Optional ScraperRequestManager instance.
            days_interval: Number of days per backscrape chunk.
            **kwargs: Additional arguments passed to parent.
        """
        super().__init__(request_manager=request_manager, **kwargs)
        self.days_interval = days_interval

        # Cache for the search form's hidden fields
        self._hidden_fields: dict[str, str] = {}

    def scrape(self) -> Generator[TexasCommonData, None, None]:
        """Scrape dockets for a date range.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        yield from self._search_date_range(start_date, end_date)

    def backfill(
        self,
        courts: list[str],
        date_range: tuple[date, date],
    ) -> Generator[TexasCommonData, None, None]:
        """Backfill dockets for multiple courts over a date range.

        Note: TAMES searches all courts at once, so the courts parameter
        is used for filtering results rather than making separate requests.
        """
        start_date, end_date = date_range

        # Generate date range chunks
        current_start = start_date
        while current_start <= end_date:
            current_end = min(
                current_start + timedelta(days=self.days_interval - 1),
                end_date,
            )

            logger.info(
                f"{self.court_id}: Backfilling {current_start} to {current_end}"
            )

            for docket in self._search_date_range(current_start, current_end):
                # Filter by court if specified
                if courts and docket.get("court_id") not in courts:
                    continue
                yield docket

            current_start = current_end + timedelta(days=1)

    def _search_date_range(
        self,
        start_date: date,
        end_date: date,
        court_ids: Optional[list[str]] = None
    ) -> Generator[TexasCommonData, None, None]:
        """Search TAMES for dockets in a date range.

        Handles the full workflow: fetch form, submit search, paginate,
        and parse case details.
        """
        # Fetch the search form to get hidden fields
        self._fetch_search_form()

        # Submit the search
        case_urls = list(self._submit_search(start_date, end_date, court_ids=court_ids))

        logger.info(
            f"{self.court_id}: Found {len(case_urls)} cases for "
            f"{start_date} to {end_date}"
        )

        # Fetch and parse each case
        for case_url in case_urls:
            docket = self._fetch_and_parse_case(case_url)
            if docket is not None:
                yield docket

    def _fetch_search_form(self) -> None:
        """Fetch the search form page and extract hidden fields."""
        response = self.request_manager.get(self.SEARCH_URL)
        response.raise_for_status()

        tree = html.fromstring(response.content)
        self._hidden_fields = self._extract_hidden_fields(tree)

    def _submit_search(
        self,
        start_date: date,
        end_date: date,
        court_ids: Optional[list[str]] = None
    ) -> Generator[str, None, None]:
        """Submit a search and yield case URLs.

        Handles result overflow (1000+ results) by splitting date ranges,
        and handles pagination.
        """
        # Format dates for the form (M/d/yyyy)
        start_str = start_date.strftime("%-m/%-d/%Y")
        end_str = end_date.strftime("%-m/%-d/%Y")

        # Build form data
        form_data = {
            **self._hidden_fields,
            # Date range fields
            "ctl00$ContentPlaceHolder1$txtDateFiledStart": start_str,
            "ctl00$ContentPlaceHolder1$txtDateFiledStart$dateInput": start_str,
            "ctl00$ContentPlaceHolder1$txtDateFiledEnd": end_str,
            "ctl00$ContentPlaceHolder1$txtDateFiledEnd$dateInput": end_str,
            # Telerik DatePicker ClientState
            "ctl00_ContentPlaceHolder1_txtDateFiledStart_dateInput_ClientState": self._make_date_client_state(
                start_date, start_str
            ),
            "ctl00_ContentPlaceHolder1_txtDateFiledEnd_dateInput_ClientState": self._make_date_client_state(
                end_date, end_str
            ),
            "ctl00_ContentPlaceHolder1_txtDateFiledStart_ClientState": '{"minDateStr":"1900-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00"}',
            "ctl00_ContentPlaceHolder1_txtDateFiledEnd_ClientState": '{"minDateStr":"1900-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00"}',
            # Submit button
            "ctl00$ContentPlaceHolder1$btnSearch": "Search",
        }
        if court_ids is not None:
            for court_id in court_ids:
                if court_id in COURT_CHECKBOX_MAPPING:
                    form_data[COURT_CHECKBOX_MAPPING[court_id]] = "on"
        else:
            # default to all courts
            form_data["ctl00$ContentPlaceHolder1$chkAllCourts"] = "on"

        # Submit the search
        response = self.request_manager.post(self.SEARCH_URL, data=form_data)
        response.raise_for_status()

        tree = html.fromstring(response.content)

        # Check for 1000-result limit
        result_count = self._get_result_count(tree)
        if result_count >= 1000:
            # Split date range and search each half
            yield from self._handle_result_overflow(start_date, end_date)
            return

        # Parse search results
        yield from self._parse_search_results(tree)

        # Handle pagination
        while self._has_next_page(tree):
            tree = self._fetch_next_page(tree)
            yield from self._parse_search_results(tree)

    def _handle_result_overflow(
        self,
        start_date: date,
        end_date: date,
        court_ids: Optional[list[str]] = None
    ) -> Generator[str, None, None]:
        """Handle case where search returns 1000+ results.

        Splits the date range in half and searches each half separately.
        """
        if (end_date - start_date).days <= 1:
            # Can't split further - log warning
            logger.warning(
                f"Search for single day {start_date} "
                "returned 1000+ results, some may be missed"
            )
            return

        # Calculate midpoint
        midpoint = start_date + (end_date - start_date) // 2

        logger.info(
            f"Splitting search {start_date} to {end_date} "
            f"at {midpoint} due to 1000-result limit"
        )

        # Re-fetch form for fresh hidden fields
        self._fetch_search_form()

        # Search first half
        yield from self._submit_search(start_date, midpoint, court_ids=court_ids)

        # Re-fetch form for fresh hidden fields
        self._fetch_search_form()

        # Search second half
        yield from self._submit_search(midpoint + timedelta(days=1), end_date, court_ids=court_ids)

    def _parse_search_results(self, tree) -> Generator[str, None, None]:
        """Parse search results and yield case URLs.
        """
        # Find result rows
        rows = tree.xpath(
            "//table[@id='ctl00_ContentPlaceHolder1_grdCases_ctl00']"
            "//tr[contains(@class, 'rgRow') or contains(@class, 'rgAltRow')]"
        )

        seen_urls = set()
        for row in rows:
            # Find case link
            case_link = row.xpath(".//a[contains(@href, 'Case')]")
            if not case_link:
                continue

            case_url = case_link[0].get("href", "")
            if not case_url or case_url in seen_urls:
                continue

            # Normalize URL - handle both absolute and relative URLs
            if not case_url.startswith("http"):
                # Relative URL - prepend base URL
                if case_url.startswith("/"):
                    case_url = f"{self.BASE_URL}{case_url}"
                else:
                    case_url = f"{self.BASE_URL}/{case_url}"

            seen_urls.add(case_url)
            yield case_url

    def _has_next_page(self, tree) -> bool:
        """Check if there are more result pages.
        """
        next_button = tree.xpath("//input[contains(@class, 'rgPageNext')]")
        current_page_has_next = tree.cssselect(".rgCurrentPage + a")
        return bool(next_button and current_page_has_next)

    def _fetch_next_page(self, tree):
        """Fetch the next page of results.
        """
        next_button = tree.xpath("//input[contains(@class, 'rgPageNext')]")[0]
        submit_name = next_button.get("name", "")
        submit_val = next_button.get("value", "")

        hidden_fields = self._extract_hidden_fields(tree)
        form_data = {**hidden_fields, submit_name: submit_val}

        response = self.request_manager.post(self.SEARCH_URL, data=form_data)
        response.raise_for_status()

        return html.fromstring(response.content)

    def _fetch_and_parse_case(
        self, case_url: str
    ) -> Optional[TexasCommonData]:
        """Fetch and parse a case detail page.
        """
        try:
            response = self.request_manager.get(case_url)
            response.raise_for_status()

            tree = html.fromstring(response.content)
            html_str = etree.tostring(tree, encoding="unicode")

            # Determine court type from URL
            court_type = self._get_court_type_from_url(case_url)

            return self._parse_case_page(html_str, court_type)

        except Exception as e:
            logger.warning(
                f"{self.court_id}: Failed to fetch/parse case at {case_url}: {e}",
                exc_info=logger.isEnabledFor(10),
            )
            return None

    def _parse_case_page(
        self,
        html_str: str,
        court_type: str,
    ) -> Optional[TexasCommonData]:
        """Parse a case detail page using the appropriate parser.
        """
        try:
            if court_type == COURT_TYPE_SUPREME:
                parser = TexasSupremeCourtScraper()
            elif court_type == COURT_TYPE_CRIMINAL_APPEALS:
                parser = TexasCourtOfCriminalAppealsScraper()
            elif court_type.startswith(COURT_TYPE_APPEALS_PREFIX):
                court_id = f"texas_{court_type}"
                parser = TexasCourtOfAppealsScraper(court_id=court_id)
            else:
                logger.warning(
                    f"{self.court_id}: Unknown court type '{court_type}', "
                    "falling back to common parser"
                )
                from juriscraper.state.texas.common import TexasCommonScraper

                parser = TexasCommonScraper()

            parser._parse_text(html_str)
            return parser.data

        except Exception as e:
            logger.warning(
                f"{self.court_id}: Failed to parse case page "
                f"(court_type={court_type}): {e}",
                exc_info=logger.isEnabledFor(10),
            )
            return None

    @staticmethod
    def _extract_hidden_fields(tree) -> dict[str, str]:
        """Form submission relies on some hidden fields.
        """
        hidden_fields = {}
        for input_elem in tree.xpath("//input[@type='hidden']"):
            name = input_elem.get("name", "")
            value = input_elem.get("value", "")
            if name:
                hidden_fields[name] = value
        return hidden_fields

    @staticmethod
    def _make_date_client_state(date_obj: date, date_str: str) -> str:
        """Include the extraneous info the date picker expects/uses
        """
        date_formatted = date_obj.strftime("%Y-%m-%d")
        return (
            '{"enabled":true,"emptyMessage":"",'
            f'"validationText":"{date_formatted}-00-00-00",'
            f'"valueAsString":"{date_formatted}-00-00-00",'
            '"minDateStr":"1900-01-01-00-00-00",'
            '"maxDateStr":"2099-12-31-00-00-00",'
            f'"lastSetTextBoxValue":"{date_str}"'
            "}"
        )

    @staticmethod
    def _get_result_count(tree) -> int:
        """Extract result count from search results.
        """
        info_div = tree.xpath(
            "//div[contains(@class, 'rgWrap') and contains(@class, 'rgInfoPart')]"
        )
        if info_div:
            info_text = info_div[0].text_content().strip()
            match = re.search(
                r"(\d+)\s+items?\s+in\s+\d+\s+pages?", info_text, re.IGNORECASE
            )
            if match:
                return int(match.group(1))
        return 0

    @staticmethod
    def _get_court_type_from_url(case_url: str) -> str:
        """Extract court type identifier from case URL.

        TAMES URLs contain a 'coa' parameter indicating court type:
        - cossup: Supreme Court
        - coscca: Court of Criminal Appeals
        - coa01-coa15: Courts of Appeals
        """
        parsed = urlparse(case_url)
        params = parse_qs(parsed.query)
        court_type = params.get("coa", [""])[0].lower()
        return court_type
