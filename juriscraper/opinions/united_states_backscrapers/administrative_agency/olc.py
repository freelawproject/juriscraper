"""Backscraper for Dept of Justice Office of Legal Counsel
CourtID: olc
Court Short Name: OLC
Author: William E. Palin
History:
    2022-01-14: Created by William E. Palin
"""

from juriscraper.opinions.united_states.administrative_agency import olc


class Site(olc.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = range(1, 36)

    def _download_backwards(self, page: int) -> None:
        """Download backwards over the volume links in the DOJ OLC website.

        :param page: The page index for the URL
        :return: None
        """
        self.url = f"https://www.justice.gov/olc/opinions?items_per_page=40&page={page}"
        self.html = self._download()
        self._process_html()
