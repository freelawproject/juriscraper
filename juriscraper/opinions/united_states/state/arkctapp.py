# Author: Michael Lissner
# Date created: 2013-08-10

import re
from datetime import date, datetime

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import ark


class Site(ark.Site):
    court_code = "143"
    cite_regex = re.compile(r"\d{2,4} Ark\. App\. \d+", re.I)
    first_opinion_date = datetime(1979, 9, 4)

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
