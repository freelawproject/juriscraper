"""Backscraper for Supreme Court of Maine 2013
CourtID: me
Court Short Name: Me.
Author: Brian W. Carver
Date created: June 20, 2014
"""

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import me


class Site(me.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.courts.maine.gov/opinions_orders/supreme/lawcourt/2013/2013_index.shtml"
