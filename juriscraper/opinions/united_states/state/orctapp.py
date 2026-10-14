"""
Scraper for Oregon Court of Appeals
CourtID: orctapp
Court Short Name: OR Ct App
Author: William Palin
History:
    - 2023-11-18: Created
"""

from datetime import date
from importlib import import_module

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker

# `or` is a python reserved keyword; can't import the module as usual
oregon_module = import_module("juriscraper.opinions.united_states.state.or")


class Site(oregon_module.Site):
    court_code = "p17027coll5"
    citation_field = "identia"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
