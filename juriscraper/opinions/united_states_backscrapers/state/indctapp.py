"""
Backscraper for Indiana Court of Appeals
CourtID: indctapp
Court Short Name: Ind. Ct. App.
Auth: Jon Andersen <janderse@gmail.com>
Reviewer: mlr
History:
    2014-09-02: Created by Jon Andersen
"""

from juriscraper.opinions.united_states_backscrapers.state import ind


class Site(ind.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.in.gov/judiciary/opinions/archapp.html"
        self.back_scrape_iterable = (
            "archapp2010.html",
            "archapp2008.html",
            "archapp2005.html",
        )

    async def _download_backwards(self, page):
        self.url = f"http://www.in.gov/judiciary/opinions/{page}"
        self.html = await self._download()
