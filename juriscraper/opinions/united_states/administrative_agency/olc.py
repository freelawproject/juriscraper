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
        for row in self.html.xpath(".//article"):
            name = row.xpath(".//h2")[0].text_content().strip()
            url = row.xpath(".//a/@href")[0]
            date = row.xpath(".//time")[0].text_content()
            if not name:
                continue
            summary = row.xpath(".//p")[0].text_content()
            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "url": url,
                    "summary": summary,
                    "docket": "",  # Docket numbers don't appear to exist.
                }
            )
