"""Scraper for Louisiana Court of Appeal, First Circuit
CourtID: lactapp_1
Court Short Name: La. Ct. App. 1st Cir.
Author: mmantel
History:
  2019-11-24: Created by mmantel
"""

import re
from datetime import date, datetime

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import (
    get_row_column_links,
    get_row_column_text,
)
from juriscraper.lib.utils import backscrape_over_paginated_results
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = datetime(2006, 11, 3)
    # Ensure the backscrape iterable has a single item
    days_interval = (datetime.today() - first_opinion_date).days + 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        page_size = 50
        self.base_url = f"https://www.la-fcca.org/opiniongrid/opinionpub.php?opinionpage_size={page_size}"
        self.url = self.base_url
        self.make_backscrape_iterable(kwargs)
        self.is_backscrape = False

        # The opinions page does not indicate whether a case is
        # published or unpublished. That is only found in the PDF.
        # (Unpublished cases have "Not Designated For Publication" on
        # the cover page.)
        self.status = "Unknown"
        self.cipher = "AES128-SHA"
        self.set_custom_adapter(self.cipher)

    def _process_html(self):
        for row in self.html.cssselect("#opinion_contentTable tbody tr"):
            self.cases.append(
                {
                    "date": get_row_column_text(row, 1).replace(" ", ""),
                    "docket": self._parse_docket_numbers(row),
                    "name": get_row_column_text(row, 4),
                    "url": get_row_column_links(row, 3),
                }
            )

    def _parse_docket_numbers(self, row):
        # Handle cases such as:
        # "2018CA1765<br>Rehearing<br>Application"
        #     => "2018CA1765"
        # "2018CA1742<br>Consolidated With<br>2018CA1743"
        #     => "2018CA1742, 2018CA1743"
        text = get_row_column_text(row, 2)
        case_numbers = re.findall("[0-9]{4}[A-Z]{2}[0-9]{4}", text)
        return ", ".join(case_numbers)

    def _download_backwards(self, dates: tuple[date]) -> None:
        logger.info("Backscraping for range %s %s", *dates)
        url_template = f"{self.base_url}&opinionp={{}}"
        start, end = dates
        last_page = 500  # Real last page is 467 in Oct, 2024
        self.cases = backscrape_over_paginated_results(
            2, last_page, start, end, "%m/%d/%Y", self, None, url_template
        )
