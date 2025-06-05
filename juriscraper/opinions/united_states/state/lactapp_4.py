"""Scraper for Louisiana Court of Appeal, fourth Circuit
CourtID: lactapp_4
Court Short Name: La. Ct. App. 4th Cir.
Author: Luis-manzur
History:
  2025-04-22: Created by Luis-manzur
"""

import re
from datetime import date, datetime

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.string_utils import titlecase
from juriscraper.lib.type_utils import OpinionType
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = datetime(2019, 7, 17)
    days_interval = 28  # ensure a tick for each month
    date_regex = re.compile(r"\d{2}/\d{2}/\d{4}")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.la4th.org/Default.aspx"
        self.search_is_configured = False
        self.target_date = datetime(2025, 5, 1)
        self.make_backscrape_iterable(kwargs)
        self.status = "Published"
        self.parameters = {}

    def _process_html(self):
        """Process the HTML to extract case details."""

        # XPath for the opinion results
        opinion_results_xpath = "//div[contains(@class, 'opinion-result')]"
        results = self.html.xpath(opinion_results_xpath)

        # Log the number of results found
        logger.info("Found %d results on the page.", len(results))

        self.cases = []
        for result in results:
            docket = result.xpath(".//strong/text()")[0]
            name = result.xpath(".//p[not(strong)]/text()")[0]
            decree = result.xpath(
                ".//p[strong[contains(text(), 'Decree')]]/text()"
            )[0]
            date = result.xpath(
                ".//p[strong[contains(text(), 'Opinion Date')]]/text()"
            )[0]
            download_url = result.xpath(
                ".//p/a[contains(text(), 'View Document')]/@href"
            )[0]

            # Clean and structure the extracted data
            case = {
                "docket": docket if docket else None,
                "name": titlecase(name) if name else None,
                "disposition": titlecase(decree) if decree else None,
                "date": date if date else None,
                "url": download_url if download_url else None,
            }

            self.cases.append(case)

    def update_date_filters(self) -> None:
        """Set year and month values from `self.target_date`
        into self.parameters for POST use
        """
        logger.info(
            "Scraping for year: %s - month: %s",
            self.target_date.year,
            self.target_date.month,
        )

        month_name = self.target_date.strftime("%B")

        self.parameters.update(
            {
                "ctl00$Main$ddlOpMonth": month_name,
                "ctl00$Main$ddlOpYear": str(self.target_date.year),
                "__EVENTTARGET": "ctl00$Main$btnOpMonthYearSearch",
                "__EVENTARGUMENT": "",
            }
        )

        self.update_hidden_inputs()

    def update_hidden_inputs(self) -> None:
        """Parse form values characteristic of aspx sites,
        and put them in self.parameters for POST use."""
        for input in self.html.xpath('//input[@type="hidden"][@name]'):
            name = input.get("name")
            value = input.get("value", "")

            self.parameters[name] = value

    def _download_backwards(self, target_date: date) -> None:
        self.target_date = target_date
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs):
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )

    def _download(self, request_dict=None):
        if not self.test_mode_enabled():
            if not self.search_is_configured:
                self.method = "GET"
                self.html = super()._download()
                self.search_is_configured = True

            self.update_date_filters()
            self.update_hidden_inputs()
            self.method = "POST"
        return super()._download()

    def extract_from_text(self, scraped_text: str) -> dict:
        """
        Extracts structured metadata from the provided opinion text.

        Args:
            scraped_text (str): The raw text content of a judicial opinion.

        Returns:
            dict: A dictionary containing extracted metadata, including:
                - Opinion: Information about the opinion's author and type.
                - OpinionCluster: Information about the panel of judges, if available.

        Extraction details:
            - Author: Detected by a pattern of asterisks surrounding the name.
            - Opinion type: Determined by keywords in the text if author is not found.
            - Judges: Extracted from a parenthetical listing the court panel.
        """
        metadata = {}
        opinion_cluster = {}
        opinion = {}

        # Extract author information
        match = re.search(
            r"\*{6,}\s*([A-Za-z .\-']+)\s*\*{6,}", scraped_text, re.IGNORECASE
        )
        author = match.group(1).strip() if match else ""
        if author:
            opinion["author_str"] = titlecase(author)
            opinion_type = OpinionType.MAJORITY
        else:
            parts = re.split(r"\*{7,}", scraped_text, maxsplit=1)
            text = parts[1].lower() if len(parts) > 1 else ""
            if "in part" in text:
                opinion_type = (
                    OpinionType.CONCURRING_IN_PART_AND_DISSENTING_IN_PART
                )
            elif "concurs" in text or "concurring" in text:
                opinion_type = OpinionType.CONCURRENCE
            elif "dissents" in text or "dissenting" in text:
                opinion_type = OpinionType.DISSENT
            else:
                opinion_type = None
        opinion["type"] = opinion_type.value if opinion_type else ""

        # Extract court panel judges
        court_panel_match = re.search(
            r"\(Court composed of (.*?)\)", scraped_text, re.DOTALL
        )
        if court_panel_match:
            judges = court_panel_match.group(1)
            judges = re.sub(r"Judge\s+", "", judges)
            judges = re.sub(r"\s+", " ", judges)
            judges = judges.replace(",", ";").strip()
            if judges:
                opinion_cluster["judges"] = judges

        if opinion_cluster:
            metadata["OpinionCluster"] = opinion_cluster
        if opinion:
            metadata["Opinion"] = opinion

        return metadata
