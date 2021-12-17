"""
Scraper for Utah Court of Appeals
CourtID: utahctapp
Court Short Name: UT Ct. App.
History:
 2021-12-16  Created by William Palin
"""
from datetime import date

from juriscraper.opinions.united_states.state import utahctapp


class Site(utahctapp.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.back_scrape_iterable = list(range(2012, date.today().year))

    def _download_backwards(self, year: str) -> None:
        """Download the page for each year in the backscrape_iterable.

        :param year: The year to download
        :return: None
        """
        ending = "htm" if int(year) <= 2014 else "asp"
        self.url = (
            f"https://www.utcourts.gov/opinions/appopin/index-{year}.{ending}"
        )
        self.html = self._download()
        self._process_html()
