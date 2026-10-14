"""Scraper for Army Court of Criminal Appeals
CourtID: acca
Reviewer: None
History:
  2015-01-08: Created by mlr
"""

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.federal_special import acca_p


class Site(acca_p.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "https://www.jagcnet.army.mil/ACCALibrary/cases/opinions/SD"
        self.court_id = self.__module__
        self.status = "Unpublished"
