"""Backscraper for Board of Immigration Appeals
CourtID: bia
Court Short Name: BIA.
Author: William E. Palin
Date created: December 27, 2021
"""

from juriscraper.opinions.united_states.administrative_agency import bia


class Site(bia.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = range(0, 21)

    def _download_backwards(self, volume: int) -> None:
        """Download backwards over the volume links in the DOJ BIA website.

        :param volume: The volume index for the URL
        :return: None
        """
        self.volume = volume
        if not self.urls:
            self.html = self._download()
        self._process_html()
