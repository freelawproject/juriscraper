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
                    "docket": docket,
                }
            )

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request
        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.set_url(*dates)
        self.html = self._download()
        self._process_html()

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        """Formats and sets `self.url` with date inputs
        If no start or end dates are given, scrape without date filter values

        There is a Document Type filter available, with an 'Opinion' value, that
        can be added to params like this:
            {"f[1]": "document_type:94"}a
        However, we are not using it since some documents marked as 'Decisions'
        also contain opinions. For example:
        https://www.vermontjudiciary.org/sites/default/files/documents/2020-10-13-57.pdf
        titled "Opinion and Order on Cross-Motions for Summary Judgment"
        has 8 pages, most of which are argumentation

        :param start: start date
        :param end: end date
        :return None
        """
        params = {
            "facet_from_date": "",
            "facet_to_date": "",
            "f[0]": f"court_division_opinions_library_:{self.division}",  # filter by court
        }
        if start:
            params["facet_from_date"] = start.strftime("%m/%d/%Y")
            params["facet_to_date"] = end.strftime("%m/%d/%Y")

        self.url = f"{self.base_url}?{urlencode(params)}"

    def extract_from_text(self, scraped_text: str):
        match = re.search(r"\d{4} VT \d+", scraped_text[:1000])
        if match:
            return {"Citation": match.group(0)}

        return {}
