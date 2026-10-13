"""Scraper for Court of Appeals of Kentucky
CourtID: kyctapp
Court Short Name: Ky. Ct. App.
Contact: https://courts.ky.gov/aoc/technologyservices/Pages/ContactTS.aspx

"""

from datetime import date

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import ky


class Site(ky.Site):
    api_court = "Kentucky Court of Appeals"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
