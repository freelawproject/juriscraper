"""
Scraper for Indiana Court of Appeals
CourtID: indctapp
Court Short Name: Ind. Ct. App.
Auth: Jon Andersen <janderse@gmail.com>
Reviewer: mlr
History:
    2014-09-03: Created by Jon Andersen
"""

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import ind


class Site(ind.Site):
    page_court_id = "9530"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.court_name = "Court of Appeals"
