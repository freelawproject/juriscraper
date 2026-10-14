from typing_extensions import Unpack

from juriscraper.AbstractSite import BackscrapeItem, SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import utah
from juriscraper.OpinionSite import OpinionSite


class Site(utah.Site[BackscrapeItem]):
    extract_from_text = OpinionSite.extract_from_text

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[BackscrapeItem]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "https://legacy.utcourts.gov/opinions/appopin/"
        self.court_id = self.__module__
