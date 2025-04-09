"""Scraper for Louisiana Court of Appeal, Third Circuit
CourtID: lactapp_3
Court Short Name: La. Ct. App. 3rd Cir.
Author: divagnz
History:
  2025-04-08: Created by divagnz
"""
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Tuple, Optional, Dict, List

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.string_utils import format_date_with_slashes


def get_clean_text(element):
    """Extract and clean text from an lxml element."""
    return " ".join(element.text_content().split()) if element.text_content() else ""


@dataclass
class AspxWebformData:
    view_state: Optional[str]
    view_state_generator: Optional[str]
    event_validation: Optional[str]


class AspxWebformDataException(Exception):
    """Custom exception for AspxWebformData extraction errors"""

    pass


class Site(OpinionSiteLinear):
    """Scraper for Louisiana Court of Appeal, Third Circuit"""

    # First opinion date for the backscrape taken from github issue reference
    # https://github.com/freelawproject/juriscraper/issues/1197
    first_opinion_date = datetime(2017, 7, 1)
    # On this site the form allows to download opinions by month and year.
    # Setting the interval to 30 days to ensure we get all opinions, when backscraped.
    days_interval = 27

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.la3circuit.org"
        self.parameters = {}
        self.make_backscrape_iterable(kwargs)
        self.needs_special_headers = True
        self.is_aspx_wf_loaded = False
        now = datetime.now()
        self.data_regex = r".*([CKW]A\s*-\d{4}-\d{3,4}).*Opinion Date: (\d+) Case Title: ([\w \.]+) Parish: (.*) Lower Court: (.*)$"
        self.active_year = f"{date.today().year}"
        self.active_month = f"{now.strftime("%B")}"

        self.request["headers"] = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": self.url,
            "Referer": self.url,
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Brave";v="134"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "sec-gpc": "1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36",
        }

        # The opinions page does not indicate whether a case is
        # published or unpublished. That is only found in the PDF.
        self.status = "Unknown"
        self.cipher = "AES128-SHA"
        self.set_custom_adapter(self.cipher)
        self.authorization_tokens = None

    def _get_auth_data(self):
        # Always start with a GET request to establish the session and get cookies
        logger.debug("Initial GET request to establish session and obtain cookies")
        # Retrieve the initial HTML page to obtain auth_data necessary to retrieve
        # the opinions.
        self.method = "GET"
        self._request_url_get(self.url)
        self._post_process_response()
        initial_html = self._return_response_text_object()

        # Extract ASP.NET form values needed for the POST request
        viewstate = initial_html.xpath('//input[@id="__VIEWSTATE"]/@value')
        viewstategenerator = initial_html.xpath(
            '//input[@id="__VIEWSTATEGENERATOR"]/@value'
        )
        eventvalidation = initial_html.xpath('//input[@id="__EVENTVALIDATION"]/@value')
        try:
            self.auth_data = AspxWebformData(
                view_state=viewstate[0],
                view_state_generator=viewstategenerator[0],
                event_validation=eventvalidation[0],
            )
        except AspxWebformDataException:
            logger.error("Failed to extract auth data from Luisiana 3rd Circuit")
            raise

    def prepare_form_data(self, year: str, month: str):
        # Form data structure for POST requests
        self.form_data = {
            "ctl00$MainContent$ddlSearchOpinions2_Year": year,
            "ctl00$MainContent$ddlSearchOpinions2_Month": month,
            "__EVENTTARGET": "ctl00$MainContent$btnSearchOpinionsByMonthYear",
            "__VIEWSTATE": self.auth_data.view_state,
            "__VIEWSTATEGENERATOR": self.auth_data.view_state_generator,
            "__SCROLLPOSITIONX": "0",
            "__SCROLLPOSITIONY": "3000",
            "__EVENTVALIDATION": self.auth_data.event_validation,
        }

    def _download(self):
        """Override the default download method to fetch data from ASPX site

        First makes a GET request to obtain cookies and VIEWSTATE, then makes the POST request
        with the proper form fields and cookies
        """
        if self.test_mode_enabled():
            self._request_url_mock(self.url)
        else:
            if not self.is_aspx_wf_loaded:
                self._get_auth_data()

            request_dict = {}
            # Add the form data to the request
            self.prepare_form_data(year=self.active_year, month=self.active_month)
            # Set up headers for the POST request
            self.parameters = self.form_data
            self.method = "POST"

            # Make the actual POST request now that we have cookies and form values
            logger.debug("Making POST request to fetch opinion data")
            self._request_url_post(self.url)
        self._post_process_response()
        return self._return_response_text_object()

    def _process_html(self):
        """Extract the opinion data from the HTML"""
        # Target the table inside the #searchModal div
        opinion_tables = self.html.xpath(
            '//div[@id="searchModal"]//table[contains(@class, "table-striped")]'
        )

        if not opinion_tables:
            logger.info("No opinion table found in HTML")
            return

        # We expect only one table with results, so take the first one
        opinion_table = opinion_tables[0]
        rows = opinion_table.xpath(".//tbody/tr")  # Get all rows in the body

        for row in rows:
            cells = row.xpath("./td")
            if len(cells) < 1:
                continue

            # The data is all within a single <td> with multiple elements
            cell = cells[0]

            # Extract the download link
            url_element = cell.xpath(".//a/@href")
            download_path = url_element[0] if url_element else None

            # Extract text content and split into lines for parsing
            text_content = get_clean_text(cell)
            compiled_pattern = re.compile(self.data_regex, re.MULTILINE | re.DOTALL)
            matched_groups = re.findall(compiled_pattern, text_content)
            if matched_groups:
                docket, date, name, parish, lower_court = matched_groups[0]
                self.cases.append(
                    {
                        "date": format_date_with_slashes(date),
                        "docket": docket.replace(" ", ""),
                        "name": name,
                        "lower_court": f"{lower_court}, {parish} Parish",
                        "url": download_path,
                    }
                )
        print(self.cases)

    def _download_backwards(self, dates: date) -> None:
        """Download opinions for a date range"""
        logger.debug("Backscraping for Year %s and Month %s", dates.year, dates.month)
        self.active_year = dates.year
        self.active_month = f'{dates.strftime("%B")}'

    def make_backscrape_iterable(self, kwargs: Dict) -> List[Tuple[date, date]]:
        """Reuse base function to get a sequence of date objects for
        each month in the interval. Then, convert them to target URLs
        and replace the self.back_scrape_iterable
        """
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(self.back_scrape_iterable)
