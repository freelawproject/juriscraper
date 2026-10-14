# Back Scraper for New York Appellate Divisions 1st Dept.
# CourtID: nyappdiv_1st
# Court Short Name: NY
# Author: Andrei Chelaru
# Reviewer:
# Date: 2015-10-30

from datetime import date

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states_backscrapers.state import ny


class Site(ny.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court = "App+Div,+1st+Dept"
        self.interval = 30
