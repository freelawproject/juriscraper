from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.federal_appellate import cadc


class Site(cadc.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        # https://media.cadc.uscourts.gov/judgments/
        self.url = "https://media.cadc.uscourts.gov/judgments/bydate/recent"
        self.status = "Unpublished"
