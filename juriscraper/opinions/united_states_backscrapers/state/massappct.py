from datetime import datetime

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states_backscrapers.state import mass


class Site(mass.Site):
    docket_number_regex = r"\d{2}-\w-\d{1,4}"
    backscrape_date_range_mapper = [
        {
            "start": datetime(2021, 7, 9),
            "end": None,
            "url": "http://masscases.com/app100-124.html",
        },
        {
            "start": datetime(2009, 8, 20),
            "end": datetime(2021, 5, 12),
            "url": "http://masscases.com/app75-99.html",
        },
    ]

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[datetime, datetime, str]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
