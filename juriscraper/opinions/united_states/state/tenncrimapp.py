"""
Scraper for the Tennessee Court of Criminal Appeals
CourtID: tennctcrimapp
Court Short Name: Tenn. Ct. Crim. App.
"""

from datetime import date, datetime

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import tenn


class Site(tenn.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.tncourts.gov/courts/court-criminal-appeals/opinions"
        )
        self.first_opinion_date = datetime(1988, 12, 8)
