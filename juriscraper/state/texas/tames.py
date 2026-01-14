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
import time
from collections.abc import Generator
from datetime import date, datetime
from typing import Final, Optional, Union
from urllib.parse import urlencode, urljoin

from lxml import html

from juriscraper.lib.log_tools import make_default_logger
from juriscraper.state.BaseStateScraper import (
    BaseStateScraper,
    HasCaseUrl,
    ScraperRequestManager,
)
from juriscraper.state.texas.common import CourtID

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

COURT_CHECKBOX_MAPPING: dict[str, str] = {
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


class TamesSearchRow(HasCaseUrl):
    """Data extracted from a TAMES search result row."""

    case_number: str
    date_filed: str
    style: str
    v: str
    case_type: str
    coa_case_number: str
    trial_court_case_number: str
    trial_court_county: str
    trial_court: str
    appellate_court: str
    court_code: str


class TAMESScraper(BaseStateScraper):
    """Scraper for Texas appellate court dockets from TAMES.

    Searches the Texas Courts case search system by date range and
    retrieves full docket information for each case.

    Attributes:
        BASE_URL: Base URL for TAMES
        SEARCH_URL: URL for the case search form
    """

    BASE_URL = "https://search.txcourts.gov"
    SEARCH_URL = f"{BASE_URL}/CaseSearch.aspx"

    # Oldest (inaccurately) dated records in TAMES
    FIRST_RECORD_DATE = date(1900, 1, 1)

    # Additional headers for ASP.NET form submission
    ADDITIONAL_HEADERS: Final[dict[str, str]] = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    COURT_IDS: Final[list[str]] = [c.value for c in CourtID]

    MAX_RESULTS_PER_SEARCH: int = 1000

    def __init__(
        self,
        request_manager: Optional[ScraperRequestManager] = None,
        **kwargs,
    ) -> None:
        """Initialize the TAMES scraper.

        Args:
            request_manager: Optional ScraperRequestManager instance.
            days_interval: Number of days per backscrape chunk.
            **kwargs: Additional arguments passed to parent.
        """
        super().__init__(request_manager=request_manager, **kwargs)
        # Cache for the search form's hidden fields
        self._hidden_fields: dict[str, str] = {}

    def scrape(self):
        pass

    def backfill(
        self,
        courts: list[str],
        date_range: tuple[date, date],
    ) -> Generator[TamesSearchRow, None, None]:
        """Backfill dockets for multiple courts over a date range.
        There are three issues that inform the structure of this method.
        1. TAMES caps results at 1000 of the most recent cases for a given search
           This means we can't just submit one big search and page through it.
        2. TAMES will, very occassionally return 0 search results for an interval
           that definitely contains some cases.
        3. The search results pages are fairly rate limited, with notification via 403
           Forbidden responses for too many requests in succession.

        To get around these limitations, we start at the most recent end of the requested
        interval, and use search windows that overlap by one day to verify completeness.
        Addidionally, we stream results out one at a time from the results so that we can
        fetch the case pages (which are not so strictly rate limited) while we are waiting
        for cooldown. At a high-level if we were to run this with a date range of
        (1900-01-01, 2026-01-12), the first while loop iteration would search that range,
        count how many cases (say 60) occur on the oldest date (say 2025-12-20) of search results,
        then use that oldest date as the new upper end of the search interval. The next while
        loop iteration would search (1900-01-01, 2025-12-20) and verify that we find 60 cases
        on the last day of the interval.
        """

        start_date, end_date = date_range
        current_end = end_date

        self._fetch_search_form()
        last_days_results = 0
        search_retries = 0
        prior_last_day_result = None
        last_seen_case_urls: set[str] = set()
        current_seen_case_urls: set[str] = set()
        overlap_start = True  # If start_date == end_date, still run the search
        while start_date < current_end or overlap_start:
            overlap_start = False
            last_seen_case_urls = current_seen_case_urls
            current_seen_case_urls = set()
            search_end = current_end
            redundant_cases = 0

            search_gen = self._submit_search(
                start_date, current_end, court_ids=courts
            )

            # First yield is always the result count (int)
            first_value = next(search_gen)
            assert isinstance(first_value, int)
            result_count: int = first_value

            received_count = 0
            new_cases = 0

            if (
                result_count == self.MAX_RESULTS_PER_SEARCH
                and start_date == current_end
            ):
                logger.warning(
                    f"Single day search returned at least {self.MAX_RESULTS_PER_SEARCH} records. Unreliable scrape."
                )

            for item in search_gen:
                # All subsequent yields are TamesSearchRow
                assert not isinstance(item, int)
                case: TamesSearchRow = item
                received_count += 1

                case_date_str = case.get("date_filed", None)
                if case_date_str:
                    try:
                        case_date = datetime.strptime(
                            case_date_str, "%m/%d/%Y"
                        ).date()
                        if case_date < current_end:
                            last_days_results = 1
                            current_end = case_date
                        else:
                            last_days_results += 1
                    except ValueError:
                        logger.warning(
                            f"Missing/malformed filing date from case:{case}"
                        )
                        pass
                if case["case_url"] in last_seen_case_urls:
                    redundant_cases += 1
                elif case["case_url"] in current_seen_case_urls:
                    continue  # Showed up twice in this search block
                else:
                    current_seen_case_urls.add(case["case_url"])
                    new_cases += 1
                    yield case

            if (
                result_count == 0 or received_count == 0
            ) and start_date < current_end:
                # Occasionally, TAMES returns 0 rows on status 200 responses that succeed a moment later
                logger.warning(
                    f"Zero rows returned on a search with expected results: {start_date} to {current_end}"
                )
                search_retries += 1
                time.sleep(search_retries)
                if search_retries <= 3:
                    continue
                else:
                    logger.error(
                        "3 retries attempted without success. Aborting."
                    )
                    return
            search_retries = 0

            log_message = f"Collected cases from {current_end} to {search_end}. {new_cases} new cases, {redundant_cases}/{prior_last_day_result} redundant, {received_count}[{result_count}] total"
            if (
                prior_last_day_result is not None
                and redundant_cases != prior_last_day_result
            ) or received_count != result_count:
                logger.warning(log_message)
            else:
                logger.info(log_message)

            prior_last_day_result = last_days_results

            # If we got less than 1k results, we're just done.
            if received_count < self.MAX_RESULTS_PER_SEARCH:
                current_end = start_date

            # The search may have some, but not all results for our first day
            if (
                received_count == self.MAX_RESULTS_PER_SEARCH
                and start_date == current_end
            ):
                overlap_start = True

    def _fetch_search_form(self) -> None:
        """Fetch the search form page and extract hidden fields."""
        response = self.request_manager.get(self.SEARCH_URL)
        response.raise_for_status()

        tree: html.HtmlElement = html.fromstring(response.content)
        self._hidden_fields = self._extract_hidden_fields(tree)

    def _submit_search(
        self,
        start_date: date,
        end_date: date,
        court_ids: Optional[list[str]] = None,
    ) -> Generator[Union[int, TamesSearchRow], None, None]:
        """Submit a search and yield results one at a time.

        Yields:
            First yield: int - the total result count as reported by TAMES
            Subsequent yields: TamesSearchRow - individual search results
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

        # Yield the result count first
        result_count = self._get_result_count(tree)
        yield result_count

        # Yield results from first page
        for search_row in self._parse_search_results(tree):
            yield search_row

        # Handle pagination - yield results from subsequent pages
        while self._has_next_page(tree):
            tree = self._fetch_next_page(tree, form_data)
            for search_row in self._parse_search_results(tree):
                yield search_row

    @staticmethod
    def _get_cell_text(cell: html.HtmlElement) -> str:
        text = cell.text_content().strip()
        # Replace non-breaking space with empty string
        if text == "\xa0" or text == "&nbsp;":
            return ""
        return text

    def _parse_search_results(
        self, tree
    ) -> Generator[TamesSearchRow, None, None]:
        """Parse search results and yield TamesSearchRow objects."""
        # Find result rows
        rows = tree.xpath(
            "//table[@id='ctl00_ContentPlaceHolder1_grdCases_ctl00']"
            "//tr[contains(@class, 'rgRow') or contains(@class, 'rgAltRow')]"
        )

        for row in rows:
            cells = row.xpath("./td")
            if len(cells) < 11:
                continue

            # Extract case link and number from first cell
            case_link = cells[0].xpath(".//a[contains(@href, 'Case')]")
            if not case_link:
                continue

            case_url = case_link[0].get("href", "")
            if not case_url:
                continue

            # Normalize URL - handle both absolute and relative URLs
            case_url = urljoin(self.BASE_URL, case_url)
            case_number = case_link[0].text_content().strip()

            yield TamesSearchRow(
                case_number=case_number,
                case_url=case_url,
                date_filed=self._get_cell_text(cells[1]),
                style=self._get_cell_text(cells[2]),
                v=self._get_cell_text(cells[3]),
                case_type=self._get_cell_text(cells[4]),
                coa_case_number=self._get_cell_text(cells[5]),
                trial_court_case_number=self._get_cell_text(cells[6]),
                trial_court_county=self._get_cell_text(cells[7]),
                trial_court=self._get_cell_text(cells[8]),
                appellate_court=self._get_cell_text(cells[9]),
                court_code=self._get_cell_text(cells[10]),
            )

    def _has_next_page(self, tree) -> bool:
        """Check if there are more result pages."""
        next_button = tree.xpath("//input[contains(@class, 'rgPageNext')]")
        current_page_has_next = tree.cssselect(".rgCurrentPage + a")
        return bool(next_button and current_page_has_next)

    def _fetch_next_page(self, tree, form_data):
        """Fetch the next page of results."""
        next_button = tree.xpath("//input[contains(@class, 'rgPageNext')]")[0]
        submit_name = next_button.get("name", "")
        submit_val = next_button.get("value", "")

        hidden_fields = self._extract_hidden_fields(tree)
        # Hidden_fields contains some information about our current location
        # in the search results, including the page. This merge order is important.
        next_form_data = {
            **form_data,
            **hidden_fields,
            submit_name: submit_val,
        }

        response = self.request_manager.post(
            self.SEARCH_URL, data=next_form_data
        )
        response.raise_for_status()

        return html.fromstring(response.content)

    @staticmethod
    def _extract_hidden_fields(tree) -> dict[str, str]:
        """Form submission relies on some hidden fields."""
        hidden_fields = {}
        for input_elem in tree.xpath("//input[@type='hidden']"):
            name = input_elem.get("name", "")
            value = input_elem.get("value", "")
            if name:
                hidden_fields[name] = value
        return hidden_fields

    @staticmethod
    def _make_date_client_state(date_obj: date, date_str: str) -> str:
        """Include the extraneous info the date picker expects/uses"""
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
        """Extract result count from search results."""
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

    @classmethod
    def get_casemail_link(docket_number: str):
        return f"https://casemail.txcourts.gov/CaseAdd.aspx?{urlencode({'FullCaseNumber': docket_number})}"

    @classmethod
    def get_docket_link(docket_number: str):
        return f"https://search.txcourts.gov/Case.aspx?{urlencode({'cn': docket_number})}"
