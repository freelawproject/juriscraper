"""Scraper for the 10th District Court of Appeals
CourtID: ohioctap_10
Court Short Name: Ohio Dist Ct App 10
Author: Andrei Chelaru
"""

from datetime import date

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import ohio


class Site(ohio.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.court_index = 10
