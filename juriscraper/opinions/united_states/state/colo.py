"""Scraper for Colorado Supreme Court
CourtID: colo
Court Short Name: Colo.
Author: Philip Ardery
Reviewer: mlr
Date created: 2016-06-03
History:
    - 2022-01-31: Updated by William E. Palin
    - 2023-01-05: Updated by WEP
    - 2023-11-19: Drop Selenium by WEP
    - 2023-12-20: Updated with citations, judges and summaries, Palin
    - 2024-07-04: Update to new site, grossir
    - 2025-08-11: Add cleanup_content method, quevon24
"""

import re
from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

from lxml import etree, html

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import strip_bad_html_tags_insecure
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://research.coloradojudicial.gov/search.json"
    detail_url = "https://research.coloradojudicial.gov/vid/{}.json?include=abstract%2Cparent%2Cmeta%2Cformats%2Cchildren%2Cproperties_with_ids%2Clibrary%2Csource&fat=1&locale=en&hide_ct6=true&t={}"
    days_interval = 30
    first_opinion_date = datetime(2010, 1, 1)
    api_court_code = "14024_01"
    label_to_key = {
        "Docket Number": "docket",
        "Parties": "name",
        "Decision Date": "date",
        "Citation": "citation",
    }
    docket_number_regex = r"\d{2,4}(?:SC|AS|SA)\d{1,4}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.params = {
            "product_id": "COLORADO",
            "jurisdiction": "US",
            "content_type": "2",
            "court": self.api_court_code,
            "bypass_rabl": "true",
            "include": "parent,abstract,snippet,properties_with_ids",
            "per_page": "50",  # Server breaks down when per_page=500, returns 503
            "page": "1",
            "sort": "date",
            "type": "document",
            "include_local_exclusive": "true",
            "cbm": "6.0|361.0|5.0|9.0|4.0|2.0=0.01|400.0|1.0|0.001|1.5|0.2",
            "locale": "en",
            "hide_ct6": "true",
        }
        self.dates = self.update_url()
        self.request["headers"]["User-Agent"] = "Courtlistener"

        # https://www.coloradojudicial.gov/system/files/opinions-2024-11/24SC459.pdf
        # Request won't work without some of these X- headers
        self.request["headers"].update(
            {
                "X-Requested-With": "XMLHttpRequest",
                "X-Root-Account-Email": "colorado@vlex.com",
                "X-User-Email": "colorado@vlex.com",
                "X-Webapp-Seed": "9887408",
            }
        )
        self.expected_content_types = ["text/html"]
        self.make_backscrape_iterable(kwargs)

    @staticmethod
    def parse_citation(citation_str: str) -> tuple[str, str]:
        """Extract official citation from formatted citation string

        The API returns formatted strings like:
        - "People v. Kembel, 2023 CO 5, 22SA172 (Colo. Feb 21, 2023)" → "2023 CO 5"
        - "Singh v. Office, 22SC666 (Colo. Feb 21, 2023)" → "" (no official citation)
        - "Adm'r v. Comm., 527 P.3d 371 (Colo. 2023)" → "527 P.3d 371"

        :param citation_str: The formatted citation string from the API
        :return: Tuple of (citation, parallel_citation)
        """
        if not citation_str:
            return "", ""

        # Pattern for Colorado official citations: "2023 CO 5"
        co_pattern = r"\b(\d{4}\s+COA?\s+\d+)\b"
        # Pattern for Pacific Reporter citations: "527 P.3d 371" or "123 P.2d 456"
        pacific_pattern = r"\b(\d+\s+P\.\d+d\s+\d+)\b"

        citations = []

        # Find Colorado official citations
        co_match = re.search(co_pattern, citation_str)
        if co_match:
            citations.append(co_match.group(1))

        # Find Pacific Reporter citations
        pacific_match = re.search(pacific_pattern, citation_str)
        if pacific_match:
            citations.append(pacific_match.group(1))

        # Return first citation as main, second as parallel
        if len(citations) >= 2:
            return citations[0], citations[1]
        elif len(citations) == 1:
            return citations[0], ""
        else:
            return "", ""

    def update_case(self, case: dict, detail_json: dict) -> dict:
        """Update case dictionary with nested properties

        :param case: the case data
        :param detail_json: The json response
        :return: The updated case data
        """
        for p in detail_json["properties"]:
            label = p["property"]["label"]
            values = p["values"]
            if label in self.label_to_key:
                key = self.label_to_key[label]
                if label == "Citation":
                    # Parse the formatted citation string to extract only official citations
                    citation, parallel = self.parse_citation(values[0])
                    case[key] = citation
                    if parallel:
                        case["parallel_citation"] = parallel
                    # Check for additional parallel citations in values[1]
                    if len(values) > 1 and not parallel:
                        parsed_parallel, _ = self.parse_citation(values[1])
                        if parsed_parallel:
                            case["parallel_citation"] = parsed_parallel
                else:
                    case[key] = values[0]
        case["status"] = "Published" if case["citation"] else "Unpublished"
        return case

    def _process_html(self) -> None:
        search_json = self.html
        total_count = search_json["count"]
        results_in_page = len(search_json["results"])

        logger.info(
            "Number of results %s; %s in page",
            total_count,
            results_in_page,
        )

        # If we didn't get all results, try increasing per_page
        if results_in_page < total_count and not self.test_mode_enabled():
            search_json = self.update_page_size(
                total_count, results_in_page, self.dates
            )

        for result in search_json["results"]:
            case = {"citation": "", "parallel_citation": ""}
            timestamp = str(datetime.now().timestamp())[:10]
            url = self.detail_url.format(result["id"], timestamp)
            if self.test_mode_enabled():
                # we have manually nested detail JSONs to
                # to be able to have a test file
                detail_json = result["detail_json"]
            else:
                # Full case name and docket number are only available
                # on the detail page
                self._request_url_get(url)
                detail_json = self.request["response"].json()

            if (
                self.court_id
                == "juriscraper.opinions.united_states.state.colo"
            ):
                case["url"] = f"{detail_json['public_url']}/content"
            else:
                case["url"] = (
                    f"https://colorado.vlex.io/pdf_viewer/{result.get('id')}"
                )

            case = self.update_case(case, detail_json)

            # Validate required fields before appending
            required_fields = ["name", "url"]
            missing_fields = [
                field for field in required_fields if not case.get(field)
            ]
            if missing_fields:
                logger.error(
                    "Skipping case due to missing fields: %s. Detail URL: %s. Case metadata: %s",
                    ", ".join(missing_fields),
                    url,
                    case,
                )
                continue

            # Set defaults for optional fields
            if not case.get("status"):
                case["status"] = "Unknown"

            if not case.get("date"):
                case["date_filed_is_approximate"] = True
                case["date"] = self.dates[1].strftime("%Y-%m-%d")

            if not case.get("docket"):
                case["docket"] = ""
            self.cases.append(case)

    def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.dates = self.update_url(dates)
        self.html = self._download()
        self._process_html()

    def update_url(self, dates: Optional[tuple[date]] = None) -> tuple[date]:
        """
        Set URL with date filters and current timestamp.
        Request with no date filter was returning very old documents
        instead of the most recent ones

        :param dates: start and end date tuple. If not present,
            scrape last week
        :return: The dates used for the URL
        """
        if not dates:
            today = datetime.now()
            dates = (today - timedelta(7), today + timedelta(1))

        start = dates[0].strftime("%Y-%m-%d")
        end = dates[1].strftime("%Y-%m-%d")
        timestamp = str(datetime.now().timestamp())[:10]
        params = {**self.params}
        params.update(
            {
                "date": f"{start}..{end}",
                "t": timestamp,
            }
        )
        self.url = f"{self.base_url}?{urlencode(params)}"
        return dates

    @staticmethod
    def cleanup_content(content):
        """Wrap content in HTML structure if needed

        :param content: The scraped HTML
        :return: Proper HTML document
        """
        content = content.decode("utf-8")
        if "<html" not in content.lower():
            tree = strip_bad_html_tags_insecure(content, remove_scripts=True)
            new_tree = etree.Element("html")
            body = etree.SubElement(new_tree, "body")
            body.append(tree)
            return html.tostring(new_tree)

        return content.encode("utf-8")

    def update_page_size(
        self, total_count: int, results_in_page: int, dates: tuple[date]
    ) -> dict:
        new_per_page = min(
            total_count, 500
        )  # Cap at 500 to avoid server errors

        logger.info(
            "Incomplete results: got %s of %s. Retrying with per_page=%s",
            results_in_page,
            total_count,
            new_per_page,
        )
        self.params["per_page"] = str(new_per_page)
        self.update_url(dates)  # Rebuild URL with new per_page
        self.html = self._download()  # Re-download with larger page size
        search_json = self.html
        logger.info(
            "After retry: got %s of %s results",
            len(search_json["results"]),
            search_json["count"],
        )
        return search_json

    def extract_from_text(self, scraped_text: str) -> dict:
        docket_pattern = re.compile(self.docket_number_regex)
        metadata = {}
        if match := docket_pattern.search(scraped_text):
            metadata = {"Docket": {"docket_number": match.group(0)}}

        return metadata
