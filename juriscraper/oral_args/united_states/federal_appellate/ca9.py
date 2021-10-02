"""Scraper for Ninth Circuit of Appeals
CourtID: ca9
Court Short Name: ca9
"""

from juriscraper.lib.html_utils import get_row_column_text, get_row_column_links
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ca9.uscourts.gov/media/"

    def _process_html(self):
        path = "//table[@id='search-results-table']//tr"
        rows = self.html.xpath(path)

        for row in rows:

            # the last row is not valid data, but a one celled footer
            cells = row.xpath(".//td")
            if len(cells) != 7:
                continue

            self.cases.append(
                {
                    "date": get_row_column_text(row, 5),
                    "docket": get_row_column_text(row, 2),
                    "judge": get_row_column_text(row, 3),
                    "name": get_row_column_text(row, 1),
                    "url": get_row_column_links(row, 6),
                }
            )
