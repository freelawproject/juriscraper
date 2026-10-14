"""Scraper for Connecticut Appellate Court
CourtID: connctapp
Court Short Name: Connappct.
Author: Asadullah Baig<asadullahbeg@outlook.com>
Date created: 2014-07-11
History:
    - 2022-02-02, satsuki-chan: Updated to Opinionsitelinear
    - 2023-11-20, William Palin: Updated
"""

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import conn


class Site(conn.Site):
    court_abbv = "ap"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
