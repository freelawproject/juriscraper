from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states_backscrapers.state import (
    idahoctapp_civil,
)


class Site(idahoctapp_civil.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "http://www.isc.idaho.gov/opinions/caunpub.htm"
        self.court_id = self.__module__

    @override
    def _get_precedential_statuses(self) -> list[str]:
        return ["Unpublished"] * len(self)
