"""Scraper for Ninth Circuit of Appeals
CourtID: ca9
Court Short Name: ca9
"""

from juriscraper.lib.html_utils import get_row_column_text
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ca9.uscourts.gov/media/"

    def _process_html(self):
        path = "//table[@id='search-results-table']//tr"
        rows = self.html.xpath(path)
        for row in rows[1:-2]:
            parts = row.xpath(".//td[6]/a/@href")[0].split("/")
            # the components needed to build the URL for the media file are
            # are all availble in this HTML element.  The path consisters of
            # year, month, day, and the docket number.mp3
            year = parts[-3][1:5]
            month = parts[-3][5:7]
            day = parts[-3][7:]
            docket_number = parts[-2]
            # Build URL for media file with the information we have
            # No need to traverse another page.
            url = f"https://cdn.ca9.uscourts.gov/datastore/media/{year}/{month}/{day}/{docket_number}.mp3"
            self.cases.append(
                {
                    "date": get_row_column_text(row, 5),
                    "docket": get_row_column_text(row, 2),
                    "judge": get_row_column_text(row, 3),
                    "name": get_row_column_text(row, 1),
                    "url": url,
                }
            )
