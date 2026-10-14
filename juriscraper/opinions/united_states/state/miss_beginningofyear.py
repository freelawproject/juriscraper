# Auth: mlr
# Date: 2013-04-26

from datetime import date

from lxml import html
from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import miss


class Site(miss.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[int, date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__

        # If it's the beginning of January, we need to make sure that we aren't
        # missing any late-coming cases from the previous year.
        today = date.today()
        self.url = (
            "http://courts.ms.gov/scripts/websiteX_cgi.exe/GetOpinion?"
            f"Year={today.year - 1}&Court=Supreme+Court&Submit=Submit"
        )
        beginning_of_year = (
            date(today.year, 1, 1) <= today <= date(today.year, 1, 15)
        )
        if not beginning_of_year:
            # This simply aborts the crawler.
            self.html = html.fromstring("<html></html>")
