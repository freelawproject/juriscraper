"""
Scraper for Utah Court of Appeals
CourtID: utahctapp
Court Short Name: UT Ct. App.
History:
 2021-12-16  Created by William Palin
"""

from datetime import date

from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import utahctapp


class Site(utahctapp.Site[int | str]):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int | str]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.back_scrape_iterable = list(range(2012, date.today().year))

    @override
    async def _download_backwards(self, year: int | str) -> None:
        """Download the page for each year in the backscrape_iterable.

        :param year: The year to download
        :return: None
        """
        ending = "htm" if int(year) <= 2014 else "asp"
        self.url = (
            f"https://www.utcourts.gov/opinions/appopin/index-{year}.{ending}"
        )
        self.html = await self._download()
        self._process_html()
