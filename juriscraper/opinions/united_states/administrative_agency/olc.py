"""Scraper for Dept of Justice Office of Legal Counsel
CourtID: bia
Court Short Name: Dept of Justice OLC
Author: William Palin
Reviewer:
Type:
History:
    2022-01-14: Created by William E. Palin
"""

from juriscraper.lib.html_utils import (
    get_row_column_links,
    get_row_column_text,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.justice.gov/olc/opinions?items_per_page=40"
        self.status = "Published"

    def _process_html(self):
        for row in self.html.xpath(
            ".//tr[contains(@class , 'even')] | .//tr[contains(@class , 'odd')]"
        ):
            date = get_row_column_text(row, 1)
            if "Date of Issuance" in date:
                date = date.split("\n")[-1].strip()
            name = get_row_column_text(row, 2)
            url = get_row_column_links(row, 2)
            summary = get_row_column_text(row, 3)
            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "url": url,
                    "summary": summary,
                    "docket": "",  # Docket numbers don't appear to exist.
                }
            )
