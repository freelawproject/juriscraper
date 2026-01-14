"""Scraper for the Arizona Supreme Court
CourtID: ariz
Court Short Name: Ariz.
Court Contact: aaborns@courts.az.gov

History:
    2013-04-05: Created by Michael Lissner
    2014-02-07: Revised by Taliah Mirmalek
    2026-01-05: Rewritten to use new API by Luis Manzur
"""

import re
from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import quote, urlencode, urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import get_visible_text
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.azcourts.gov"
    court_param = "Supreme"
    search_page_path = "/opinions/SearchOpinionsMemoDecs"
    first_opinion_date = datetime(1998, 1, 1)
    days_interval = 30

    # XPaths for extracting authentication values
    module_xp = "//div[@id='dnn_ContentPane']/div/a/@name"
    tab_xp = "//script[contains(text(), 'g_dnnsfState')]/text()"
    token_xp = "//input[@name='__RequestVerificationToken']/@value"

    # Static API parameters
    params = {
        "searchPhrase": "",
        "decisionType": "",
        "decisionInvolvementType": "",
        "judgeId": "",
        "caseType": "",
        "caseSubType": "",
        "constitutionalityOpinionsOnly": "false",
    }

    # Map API decision types to precedential status
    # Note: "Decord" (Decision Order) entries are procedural orders, not opinions
    status_map = {
        "Opinion": "Published",
        "Memo": "Unpublished",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=7)
        self.url = urljoin(self.base_url, self.search_page_path)
        self.make_backscrape_iterable(kwargs)
        self.opinions_url = f"{self.base_url}/API/Azcourts/Opinions/GetOpinions"

    def _build_api_url(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
        page: int = 0,
    ) -> str:
        """Build the API URL with query parameters.

        :param start_date: Start date
        :param end_date: End date
        :param page: Page number (0-indexed)
        :return: Full API URL
        """
        params = {
            **self.params,
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "court": self.court_param,
            "page": page,
        }
        return f"{self.opinions_url}?{urlencode(params)}"

    def _set_auth_headers(self) -> None:
        """Extract and set authentication headers from HTML page.

        :return: None
        """
        tab_script = self.html.xpath(self.tab_xp)[0]
        tab_id = re.search(r'"tabId":(\d+)', tab_script).group(1)

        self.request["headers"].update(
            {
                "ModuleId": self.html.xpath(self.module_xp)[0],
                "TabId": tab_id,
                "RequestVerificationToken": self.html.xpath(self.token_xp)[0],
            }
        )

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

        # Fetch search page and extract auth headers
        self.html = super()._download()
        self._set_auth_headers()

        # Build API URL and fetch JSON
        self.url = self._build_api_url(self.start_date, self.end_date)
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
            decision_type = opinion["DecisionType"]
            # Skip Decord (Decision Order) - these are procedural orders, not opinions
            if decision_type not in self.status_map:
                continue
            file_url = opinion["FileUrl"]

            html_summary = opinion["Summary"]
            summary = ""
            if html_summary:
                summary = (
                    get_visible_text(html_summary).strip()
                )
            # Normalize whitespace in summary
            summary = " ".join(summary.split())

            self.cases.append(
                {
                    "name": titlecase(opinion["Title"]),
                    "docket": opinion["CaseNumber"],
                    "date": opinion["FilingDate"],
                    "url": urljoin(self.base_url, quote(file_url, safe="/:@")),
                    "status": self.status_map.get(decision_type, "Unknown"),
                    "author": self._extract_author(
                        opinion.get("OpinionJudges", [])
                    ),
                    "summary": summary,
                }
            )

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
        author = next(
            (
                p
                for p in judges
                if p.get("DecisionInvolvementType") == "Author"
            ),
            None,
        )
        if not author:
            return ""
        name = f"{author.get('FirstName', '')} {author.get('MiddleName', '')} {author.get('LastName', '')}".strip()
        name = " ".join(name.split())  # Normalize whitespace
        if author.get("Suffix"):
            name = f"{name}, {author['Suffix']}"
        return name

    def _fetch_next_page(self, page: int) -> None:
        """Fetch next page of results.

        Auth headers are already set from the initial download.

        :param page: Page number to fetch from
        :return: None
        """
        self.url = self._build_api_url(self.start_date, self.end_date, page)
        self.html = super()._download()
        self._process_html()

    def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Make custom date range request for backscraping.

        :param dates: (start_date, end_date) tuple
        :return: None
        """
        self.start_date, self.end_date = dates
        logger.info(
            "Backscraping for range %s to %s", self.start_date, self.end_date
        )

        # Reset URL to search page so _download fetches fresh auth tokens
        self.url = urljoin(self.base_url, self.search_page_path)
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
