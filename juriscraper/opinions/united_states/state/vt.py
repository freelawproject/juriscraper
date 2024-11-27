"""Scraper for Vermont Supreme Court
CourtID: vt
Court Short Name: VT
Court Contact: submit form here https://www.vermontjudiciary.org/website-feedback-form

If there are errors with the site, you can contact:

 Monica Bombard
 (802) 828-4784

She's very responsive.
"""

import re
from datetime import date, datetime
from typing import Optional, Tuple
from urllib.parse import urlencode

from lxml import html

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.vermontjudiciary.org/opinions-decisions"
    days_interval = 30
    first_opinion_date = datetime(2000, 1, 1)
    division = 7

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        if self.division == 7:
            self.first_opinion_date = datetime(1999, 5, 26)
        self.status = "Published"
        self.set_url()
        self.make_backscrape_iterable(kwargs)
        self.needs_special_headers = True
        self.request["headers"] = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }

    def _process_html(self) -> None:
        """Process HTML into case dictionaries
        Source's page size is 25 rows
        :return None
        """
        for case in self.html.xpath(".//article"):
            name_url_span = case.xpath(
                ".//div[contains(@class, 'views-field-name')]"
            )[0]
            date_filed = (
                case.xpath(
                    ".//div[contains(@class, 'views-field-field-document-expiration')]"
                )[0]
                .text_content()
                .strip()
            )
            docket = (
                case.xpath(
                    ".//div[contains(@class, 'views-field-field-document-number')]"
                )[0]
                .text_content()
                .strip()
            )
            self.cases.append(
                {
                    "url": name_url_span.xpath(".//a/@href")[0],
                    "name": titlecase(name_url_span.text_content()),
                    "date": date_filed,
                    "docket": [docket],
                }
            )

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Download data for a given date range, handling pagination."""
        logger.info("Backscraping for range %s %s", *dates)
        page = 0
        total_cases = 0
        while True:
            logger.info(f"Fetching page {page} for range {dates}")
            self.set_url(*dates, page=page)
            self.html = self._download()
            cases_before = len(self.cases)
            self._process_html()
            cases_after = len(self.cases)
            if cases_after == cases_before:
                logger.info("No more cases found. Stopping pagination.")
                break
            page += 1
            total_cases += cases_after - cases_before

        logger.info(f"Total cases scraped: {total_cases}")

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None,
        page: int = 0
    ) -> None:
        params = {
            "facet_from_date": "",
            "facet_to_date": "",
            "f[0]": f"court_division_opinions_library_:{self.division}",
            # Filter by court
            "search_api_fulltext": "",
            "page": page,
        }
        if start:
            params["facet_from_date"] = start.strftime("%m/%d/%Y")
            params["facet_to_date"] = end.strftime("%m/%d/%Y")

        self.url = f"{self.base_url}?{urlencode(params)}"

    def extract_from_text(self, scraped_text: str):
        match = re.search(
            r"(?P<volume>\d{4}) (?P<reporter>VT) (?P<page>\d+)",
            scraped_text[:1000],
        )
        if match:
            return {"Citation": {"type": 8, **match.groupdict()}}

        return {}

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        print(f"{start_date} , {end_date}")
        self._download_backwards((start_date,end_date))

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return len(self.cases)

    def get_court_type(self):
        return "state"

    def get_class_name(self):
        return "vt"

    def get_state_name(self):
        return "Vermont"

    def get_court_name(self):
        return "Supreme Court of Vermont"
