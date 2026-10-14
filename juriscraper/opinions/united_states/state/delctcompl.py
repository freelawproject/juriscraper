#  Scraper for the Court Of Common Pleas of Delaware
# CourtID: dectcompl
# Court Short Name: De.
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 31 July 2014

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import delaware
from juriscraper.OpinionSite import OpinionSite


class Site(delaware.Site):
    extract_from_text = OpinionSite.extract_from_text

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "https://courts.delaware.gov/opinions/List.aspx?ag=Court%20of%20Common%20Pleas"
        self.court_id = self.__module__
