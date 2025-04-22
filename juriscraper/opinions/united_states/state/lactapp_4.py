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
        self.target_date = datetime(2025, 1, 1)
        self.make_backscrape_iterable(kwargs)
        self.status = "Unknown"
        self.parameters = {}

    def _process_html(self):
        """Process the HTML to extract case details."""

        if not self.test_mode_enabled():
            self.method = "POST"

            # We need to set the proper search filter the first time
            if not self.search_is_configured:
                # First perform a GET request to get initial form values
                self.method = "GET"
                self.html = self._download()
                self.update_hidden_inputs()
                self.search_is_configured = True
                self.method = "POST"

            # Set the proper filters to get the actual data we want
            self.update_date_filters()
            self.html = self._download()

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
                "name": name if name else None,
                "disposition": decree if decree else None,
                "date": date if date else None,
                "url": download_url if download_url else None,
            }

            # Append the case to the list of cases
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

        month_names = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        month_name = month_names[self.target_date.month - 1]

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
        for input in self.html.xpath('//input[@type="hidden"]'):
            name = input.get("name")
            value = input.get("value", "")
            if name:
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
