from datetime import date, datetime

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import nj
from juriscraper.OpinionSite import OpinionSite


class Site(nj.Site):
    first_opinion_date = datetime(2017, 5, 25)
    extract_from_text = OpinionSite.extract_from_text

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.base_url = self.url = (
            "https://www.njcourts.gov/attorneys/opinions/published-tax"
        )
        self.status = "Published"
