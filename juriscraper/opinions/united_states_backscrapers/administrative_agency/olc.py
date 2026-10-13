"""Backscraper for Dept of Justice Office of Legal Counsel
CourtID: olc
Court Short Name: OLC
Author: William E. Palin
History:
    2022-01-14: Created by William E. Palin
"""

from datetime import date

from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.administrative_agency import olc


class Site(olc.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date] | int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = range(1, 36)

    @override
    async def _download_backwards(
        self, dates: tuple[date, date] | int
    ) -> None:
        """Download backwards over the volume links in the DOJ OLC website.

        :param page: The page index for the URL
        :return: None
        """
        if not isinstance(dates, int):
            raise TypeError("Expected int for backfill argument page")
        page = dates
        self.url = f"https://www.justice.gov/olc/opinions?items_per_page=40&page={page}"
        self.html = await self._download()
        self._process_html()
