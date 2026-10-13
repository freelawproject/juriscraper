"""
Scraper for New York Court of Appeals
CourtID: ny
Court Short Name: NY
History:
 2015-10-27  Created by Andrei Chelaru
"""

from datetime import date

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state.nyappterm_1st import (
    Site as NySite,
)


class Site(NySite):
    first_opinion_date = date(2003, 10, 27)
    days_interval = 180

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court = "Court of Appeals"
