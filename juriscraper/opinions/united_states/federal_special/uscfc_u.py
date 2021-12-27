"""Scraper for the United States Court of Federal Claims
CourtID: uscfc
Court Short Name: Fed. Cl."""

from juriscraper.opinions.united_states.federal_special import uscfc


class Site(uscfc.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.uscfc.uscourts.gov/aggregator/sources/10"
        self.court_id = self.__module__
        self.back_scrape_iterable = list(range(1, 2))

    def _get_precedential_statuses(self):
        return ["Unpublished"] * len(self.case_names)

    def _download_backwards(self, page):
        self.url = (
            f"http://www.uscfc.uscourts.gov/aggregator/sources/10?page={page}"
        )
        self.html = self._download()
