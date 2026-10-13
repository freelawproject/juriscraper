"""Backscraper for Supreme Court of Maine 2021 redux
CourtID: me
Court Short Name: Me.
Author: William E. Palin
Date created: March 31, 2021
"""

from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import me


class Site(me.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = [2020, 2019, 2018, 2017]

    @override
    async def _download_backwards(self, year: int) -> None:
        self.url = f"https://www.courts.maine.gov/courts/sjc/lawcourt/{year}/index.html"
        self.html = await self._download()
