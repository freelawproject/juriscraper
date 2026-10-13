from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.federal_appellate import ca6


class Site(ca6.Site):
    bap_scraper = True

    # See https://www.ca6.uscourts.gov/bankruptcy-appellate-panel
    initials_to_judges = {
        "RSM": "Randal S. Mashburn",
        "SHB": "Suzanne H. Bauknight",
        "JLC": "Jimmy Croom",
        "JTG": "John T. Gregg",
        "JPG": "John P. Gustafson",
        "CRM": "Charles R. Merrill",
    }

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.should_have_results = False
