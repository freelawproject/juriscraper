"""
Scraper for all Texas court dockets from TAMES.

CourtID: tex
Court Short Name: TX
Website: https://search.txcourts.gov/CaseSearch.aspx

This scraper searches the Texas Courts case search system (TAMES) and
retrieves docket information for cases from all Texas appellate courts:
- Supreme Court
- Court of Criminal Appeals
- Courts of Appeals (1st through 15th districts)

It uses the existing parser classes in juriscraper/state/texas/.

"""

import re
from datetime import date, timedelta
from typing import Optional
from urllib.parse import parse_qs, urlparse

from juriscraper.DocketSite import DocketSite
from juriscraper.lib.html_utils import fix_links_in_lxml_tree
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.state.texas.common import TexasCommonData
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


class Site(DocketSite):
    """Scraper for all Texas appellate court dockets from TAMES.

    Searches the Texas Courts case search system by date range and
    retrieves full docket information for each case from all courts.

    Attributes:
        BASE_URL: Base URL for TAMES
        ENTRY_URL: URL for the case search form
    """

    BASE_URL = "https://search.txcourts.gov"
    ENTRY_URL = f"{BASE_URL}/CaseSearch.aspx"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.ENTRY_URL

        # Backscraping configuration
        # Oldest accurately dated record is 1902-12-09
        # Oldest inaccurately date record is 1900-01-01
        # Note: AbstractSite.make_backscrape_iterable expects `first_opinion_date`
        self.first_opinion_date = date(1900, 1, 1)
        self.days_interval = (
            7  # Weekly intervals to try to stay under 1000-result limit
        )

        # Track state for multi-step scraping
        self._search_start_date: Optional[date] = None
        self._search_end_date: Optional[date] = None
        self._case_urls: list[str] = []

        # Initialize backscrape iterable if kwargs provided
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        # Default to last 7 days for normal scraping
        if self._search_end_date is None:
            self._search_end_date = date.today()
        if self._search_start_date is None:
            self._search_start_date = self._search_end_date - timedelta(days=7)

        self._submit_search(self._search_start_date, self._search_end_date)

    def _submit_search(self, start_date: date, end_date: date) -> None:
        """Submit the search form and collect case URLs.

        Args:
            start_date: Start of date range to search
            end_date: End of date range to search
        """
        # Extract hidden fields from the form
        hidden_fields = self._extract_hidden_fields()

        # Format dates for the form (M/d/yyyy)
        start_str = start_date.strftime("%-m/%-d/%Y")
        end_str = end_date.strftime("%-m/%-d/%Y")

        # Build form data
        form_data = {
            **hidden_fields,
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
            # Select all courts checkbox
            "ctl00$ContentPlaceHolder1$chkAllCourts": "on",
            # Submit button
            "ctl00$ContentPlaceHolder1$btnSearch": "Search",
        }

        # Submit the search
        self.method = "POST"
        self.parameters = form_data
        self.request["headers"]["Content-Type"] = (
            "application/x-www-form-urlencoded"
        )

        html = self._download()

        # Check for 1000-result limit
        result_count = self._get_result_count(html)
        if result_count >= 1000:
            # Split date range and search again
            self._handle_result_overflow(start_date, end_date)
            return

        # Parse search results and collect case URLs
        self._parse_search_results(html)

        # Handle pagination
        while self._has_next_page(html):
            html = self._fetch_next_page(html)
            self._parse_search_results(html)

        # Fetch and parse each case
        self._fetch_case_details()

    def _extract_hidden_fields(self) -> dict[str, str]:
        """They be tryin to hide things.
        """
        hidden_fields = {}
        for input_elem in self.html.xpath("//input[@type='hidden']"):
            name = input_elem.get("name", "")
            value = input_elem.get("value", "")
            if name:
                hidden_fields[name] = value
        return hidden_fields

    @staticmethod
    def _make_date_client_state(date_obj: date, date_str: str) -> str:
        """A wad of data that's mostly extraneous to our concerns.
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

    def _get_result_count(self, html) -> int:
        info_div = html.xpath(
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

    def _handle_result_overflow(
        self, start_date: date, end_date: date
    ) -> None:
        """Handle case where search returns 1000+ results.

        Splits the date range in half and searches each half separately.
        Returns if 
        """
        if (end_date - start_date).days <= 1:
            # Can't split further - just log warning and continue
            logger.warning(
                f"{self.court_id}: Search for single day {start_date} "
                "returned 1000+ results, some may be missed"
            )
            raise Exception("Single day with 1k+ results. Fundamental assumption broken.")

        midpoint = start_date + (end_date - start_date) // 2

        logger.info(
            f"{self.court_id}: Splitting search {start_date} to {end_date} "
            f"at {midpoint} due to 1000-result limit"
        )

        # Search first half
        self._submit_search(start_date, midpoint)

        # Search second half
        self._submit_search(midpoint + timedelta(days=1), end_date)

    def _parse_search_results(self, html) -> None:
        """Parse search results and collect case URLs.

        Args:
            html: Parsed HTML tree
        """
        # Fix links to be absolute
        if hasattr(html, "rewrite_links"):
            html.rewrite_links(fix_links_in_lxml_tree, base_href=self.BASE_URL)

        # Find search result rows
        rows = html.xpath(
            "//table[@id='ctl00_ContentPlaceHolder1_grdCases_ctl00']"
            "//tr[contains(@class, 'rgRow') or contains(@class, 'rgAltRow')]"
        )

        for row in rows:
            # Find case link
            case_link = row.xpath(".//a[contains(@href, 'Case')]")
            if not case_link:
                continue

            case_url = case_link[0].get("href", "")
            if case_url and case_url not in self._case_urls:
                # Normalize URL
                if case_url.startswith("/"):
                    case_url = f"{self.BASE_URL}{case_url}"
                self._case_urls.append(case_url)

    def _has_next_page(self, html) -> bool:
        """Check for the presence of that nextpage input. 
        """
        next_button = html.xpath("//input[contains(@class, 'rgPageNext')]")
        current_page_has_next = html.cssselect(".rgCurrentPage + a")
        return bool(next_button and current_page_has_next)

    def _fetch_next_page(self, html):
        """Fetch the next page of results.
        """
        next_button = html.xpath("//input[contains(@class, 'rgPageNext')]")[0]
        submit_name = next_button.get("name", "")
        submit_val = next_button.get("value", "")

        hidden_fields = {}
        for input_elem in html.xpath("//input[@type='hidden']"):
            name = input_elem.get("name", "")
            value = input_elem.get("value", "")
            if name:
                hidden_fields[name] = value

        form_data = {**hidden_fields, submit_name: submit_val}

        self.parameters = form_data
        return super()._download()

    def _fetch_case_details(self) -> None:
        """Fetch and parse each case detail page."""
        self.method = "GET"
        self.parameters = None

        for case_url in self._case_urls:
            try:
                self.url = case_url
                case_html = super()._download()

                # Determine court type from URL and use appropriate parser
                court_type = self._get_court_type_from_url(case_url)
                docket_data = self._parse_case_page(case_html, court_type)
                if docket_data:
                    self.dockets.append(docket_data)

            except Exception as e:
                logger.warning(
                    f"{self.court_id}: Failed to parse case at {case_url}: {e}",
                    exc_info=logger.isEnabledFor(
                        10
                    ),  # Include traceback if DEBUG
                )
                continue

    @staticmethod
    def _get_court_type_from_url(case_url: str) -> str:
        """Extract court type identifier from case URL.

        TAMES URLs contain a 'coa' parameter indicating court type:
        - cossup: Supreme Court
        - coscca: Court of Criminal Appeals
        - coa01-coa15: Courts of Appeals

        Args:
            case_url: Full URL to case detail page

        Returns:
            Court type identifier string
        """
        # Parse URL to get query parameters
        parsed = urlparse(case_url)
        params = parse_qs(parsed.query)

        # 'coa' parameter contains court type
        court_type = params.get("coa", [""])[0].lower()
        return court_type

    def _parse_case_page(
        self, html, court_type: str
    ) -> TexasCommonData | None:
        """Parse a case detail page using the appropriate parser.
        """
        try:
            from lxml import etree

            # Convert tree back to string for parser
            html_str = etree.tostring(html, encoding="unicode")

            # Select parser based on court type
            if court_type == COURT_TYPE_SUPREME:
                docket_data = self._parse_supreme_court(html_str)
            elif court_type == COURT_TYPE_CRIMINAL_APPEALS:
                docket_data = self._parse_criminal_appeals(html_str)
            elif court_type.startswith(COURT_TYPE_APPEALS_PREFIX):
                docket_data = self._parse_court_of_appeals(
                    html_str, court_type
                )
            else:
                logger.warning(
                    f"{self.court_id}: Unknown court type '{court_type}', "
                    "falling back to common parser"
                )
                docket_data = self._parse_common(html_str)

            return docket_data

        except Exception as e:
            logger.warning(
                f"{self.court_id}: Failed to parse case page "
                f"(court_type={court_type}): {e}",
                exc_info=logger.isEnabledFor(10),  # Include traceback if DEBUG
            )
            return None

    def _parse_supreme_court(self, html_str: str) -> TexasCommonData:
        """Parse a Texas Supreme Court case page.
        """
        parser = TexasSupremeCourtScraper()
        parser._parse_text(html_str)
        return parser.data

    def _parse_criminal_appeals(self, html_str: str) -> TexasCommonData:
        """Parse a Texas Court of Criminal Appeals case page.
        """
        parser = TexasCourtOfCriminalAppealsScraper()
        parser._parse_text(html_str)
        return parser.data

    def _parse_court_of_appeals(
        self, html_str: str, court_type: str
    ) -> TexasCommonData:
        """Parse a Texas Court of Appeals case page.
        """
        # Convert court type to court_id format (e.g., 'coa01' -> 'texas_coa01')
        court_id = f"texas_{court_type}"
        parser = TexasCourtOfAppealsScraper(court_id=court_id)
        parser._parse_text(html_str)
        return parser.data

    def _parse_common(self, html_str: str) -> TexasCommonData:
        """Parse a case page using the common parser (fallback).
        """
        from juriscraper.state.texas.common import TexasCommonScraper

        parser = TexasCommonScraper()
        parser._parse_text(html_str)
        return parser.data

    def _download_backwards(self, date_range: tuple[date, date]) -> None:
        """Download dockets for a specific date range during backscraping.
        """
        start_date, end_date = date_range
        self._search_start_date = start_date
        self._search_end_date = end_date
        self._case_urls = []

        # Fetch the search form first
        self.method = "GET"
        self.url = self.ENTRY_URL
        self.html = super()._download()

        # Submit the search
        self._submit_search(start_date, end_date)

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Create backscrape iterable with weekly date ranges.

        Args:
            kwargs: May contain backscrape_start, backscrape_end, days_interval
        """
        super().make_backscrape_iterable(kwargs)

        if self.back_scrape_iterable:
            # Already created by parent - it's a list of (start, end) tuples
            # The parent's implementation should work fine with weekly intervals
            pass
