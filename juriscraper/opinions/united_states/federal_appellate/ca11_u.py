from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.federal_appellate import ca11_p


class Site(ca11_p.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "http://media.ca11.uscourts.gov/opinions/unpub/logname.php"
        self.court_id = self.__module__
        self.back_scrape_iterable = list(range(20, 22000, 20))
        self.should_have_results = True
        self.status = "Unpublished"
