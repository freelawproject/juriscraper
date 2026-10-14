from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import wash


class Site(wash.Site):
    crt_level = "C"
    pub_status = "PUB"
    name_td_index = 4
    type_td_index = 5

    # Example URL
    # https://www.courts.wa.gov/opinions/index.cfm?fa=opinions.byYear&fileYear=2025&crtLevel=C&pubStatus=PUB

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
