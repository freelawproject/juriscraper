"""Scraper for the Arizona Supreme Court
CourtID: ariz
Court Short Name: Ariz.

History:
    2013-04-05: Created by Michael Lissner
    2014-02-07: Revised by Taliah Mirmalek
    2026-01-05: Rewritten to use new API by Luis Manzur
"""

import re
from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.azcourts.gov"
    court_param = "Supreme"
    search_page_path = "/opinions/SearchOpinionsMemoDecs"
    first_opinion_date = datetime(1998, 1, 1)
    days_interval = 30

    # Map API decision types to precedential status
    status_map = {
        "Opinion": "Published",
        "Memo": "Unpublished",
        "Decord": "Unpublished",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.verification_token = None
        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=7)
        self.url = self._build_api_url(self.start_date, self.end_date)
        self.make_backscrape_iterable(kwargs)

    def _build_api_url(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 0,
    ) -> str:
        """Build the API URL with query parameters.

        :param start_date: Start date
        :param end_date: End date
        :param page: Page number (0-indexed)
        :return: Full API URL
        """
        params = [
            "searchPhrase=",
            f"startDate={start_date.strftime('%Y-%m-%d') or ''}",
            f"endDate={end_date.strftime('%Y-%m-%d') or ''}",
            f"court={self.court_param}",
            "decisionType=",
            "decisionInvolvementType=",
            "judgeId=",
            "caseType=",
            "caseSubType=",
            "constitutionalityOpinionsOnly=false",
            f"page={page}",
        ]
        return f"{self.base_url}/API/Azcourts/Opinions/GetOpinions?{'&'.join(params)}"

    def _get_verification_token(self) -> None:
        """Fetch the search page to get the verification token, module_id, and tab_id.

        The session cookies are automatically stored in self.request["session"].
        Sets self.verification_token, self.module_id, and self.tab_id.

        :return: None
        """
        search_url = urljoin(self.base_url, self.search_page_path)
        logger.info("Fetching verification token from %s", search_url)

        self._request_url_get(search_url)
        html_content = self.request["response"].text

        # Extract the __RequestVerificationToken from the hidden input
        token_match = re.search(
            r'name="__RequestVerificationToken"[^>]*value="([^"]+)"',
            html_content,
        )
        if not token_match:
            raise ValueError(
                "Could not find __RequestVerificationToken in page"
            )
        self.verification_token = token_match.group(1)

        # Extract tabId from g_dnnsfState JavaScript variable
        tab_match = re.search(r'"tabId":(\d+)', html_content)
        if not tab_match:
            raise ValueError("Could not find tabId in page")
        self.tab_id = tab_match.group(1)

        # Extract moduleId from app-container element
        module_match = re.search(r'app-container-(\d+)', html_content)
        if not module_match:
            raise ValueError("Could not find moduleId in page")
        self.module_id = module_match.group(1)

    def _download(self, request_dict=None):
        """Override download to add authentication headers.

        First fetches the search page to get the verification token,
        then makes the API request with proper headers.

        :param request_dict: Optional request parameters
        :return: JSON response from API
        """
        # In test mode, use the parent _download method which handles mock requests
        if self.test_mode_enabled():
            return super()._download(request_dict)

        # Get the verification token (also sets up session cookies)
        if not self.verification_token:
            self._get_verification_token()

        # Set up headers for the API request
        self.request["headers"].update(
            {
                "ModuleId": self.module_id,
                "TabId": self.tab_id,
                "RequestVerificationToken": self.verification_token,
            }
        )

        # Make the API request
        return super()._download(request_dict)

    def _process_html(self) -> None:
        """Parse API JSON response into case dictionaries.

        :return: None
        """
        json_response = self.html

        total_count = json_response.get("TotalCount", 0)
        page_index = json_response.get("PageIndex", 0)
        page_size = json_response.get("PageSize", 10)

        logger.info(
            "Processing page %d: %d total results",
            page_index + 1,
            total_count,
        )

        for opinion in json_response.get("Opinions", []):
            case_name = titlecase(opinion.get("Title", ""))
            docket = opinion.get("CaseNumber", "")
            date_filed = opinion.get("FilingDate", "")
            file_url = opinion.get("FileUrl", "")
            decision_type = opinion.get("DecisionType", "")
            html_summary = opinion.get("Summary", "")
            summary = re.sub(
                r"<[^>]+>", "", html_summary
            ).strip()  # remove html tags from summary
            # Build full URL for the PDF
            url = urljoin(self.base_url, file_url)

            # Map decision type to status
            status = self.status_map.get(decision_type, "Unknown")

            # Extract author
            author = self._extract_author(opinion.get("OpinionJudges", []))

            case = {
                "name": case_name,
                "docket": docket,
                "date": date_filed,
                "url": url,
                "status": status,
                "author": author,
                "summary": summary,
            }

            self.cases.append(case)

        # Handle pagination if not in test mode
        if not self.test_mode_enabled():
            total_pages = (total_count + page_size - 1) // page_size
            if page_index + 1 < total_pages:
                self._fetch_next_page(page_index + 1)

    def _extract_author(self, judges: list) -> str:
        """Extract the author judge from the list of opinion judges.

        :param judges: List of judge dictionaries from API
        :return: Author name or empty string
        """
        for judge in judges:
            if judge.get("DecisionInvolvementType") == "Author":
                first = judge.get("FirstName", "")
                middle = judge.get("MiddleName", "")
                last = judge.get("LastName", "")
                suffix = judge.get("Suffix", "")
                return " ".join(filter(None, [first, middle, last, suffix]))
        return ""

    def _fetch_next_page(self, page: int) -> None:
        """Fetch next page of results.

        :param page: Page number to fetch from
        :return: None
        """
        self.url = self._update_page_in_url(self.url, page)
        self.html = self._download()
        self._process_html()

    def _update_page_in_url(self, url: str, page: int) -> str:
        """Update the page parameter in a URL.

        :param url: The URL to update
        :param page: New page number
        :return: Updated URL
        """
        return re.sub(r"page=\d+", f"page={page}", url)

    def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Make custom date range request for backscraping.

        :param dates: (start_date, end_date) tuple
        :return: None
        """
        start, end = dates
        logger.info("Backscraping for range %s to %s", start, end)

        start_str = start
        end_str = end

        self.url = self._build_api_url(
            start_date=start_str, end_date=end_str, page=0
        )
        self.html = self._download()
        self._process_html()

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court and judge from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        lower_court_pattern = re.compile(
            r"""
            Appeal\s+from\s+the\s+(?P<lower_court>[^\n]+)\n\s*
            The\s+(?:Honorable\s+)?(?P<lower_court_judge>[^,]+),\s+Judge[^\n]*\n\s*
            No\.\s+(?P<lower_court_number>[^\s]+)
            """,
            re.X | re.MULTILINE | re.DOTALL,
        )

        result = {}

        if match := lower_court_pattern.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()

            lower_court_judge = match.group("lower_court_judge").strip()
            lower_court_number = match.group("lower_court_number").strip()

            if lower_court:
                result["Docket"] = {"appeal_from_str": lower_court}
            if lower_court_judge:
                result.setdefault("OriginatingCourtInformation", {})[
                    "assigned_to_str"
                ] = lower_court_judge
            if lower_court_number:
                result.setdefault("OriginatingCourtInformation", {})[
                    "docket_number"
                ] = lower_court_number

        return result
