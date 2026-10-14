"""Backscraper for Board of Immigration Appeals
CourtID: bia
Court Short Name: BIA.
Author: William E. Palin
Date created: December 27, 2021
"""

from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.administrative_agency import bia


class Site(bia.Site[int]):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = range(0, 21)

    @override
    async def _download_backwards(self, volume: int) -> None:
        """Download backwards over the volume links in the DOJ BIA website.

        :param volume: The volume index for the URL
        :return: None
        """
        self.volume = volume
        if not bool(self.urls):
            self.html = await self._download()
        await self._process_html()
