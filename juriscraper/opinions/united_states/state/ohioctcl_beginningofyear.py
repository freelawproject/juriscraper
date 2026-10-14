# Auth: arderyp
# Date: 2017-01-26

from datetime import date

from lxml import html
from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import ohioctcl


class Site(ohioctcl.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__

        # If it's January, we need to make sure that we aren't
        # missing any late-coming cases from the previous year.
        today = date.today()
        if today.month == 1:
            self.year = today.year - 1
        else:
            # This simply aborts the crawler.
            self.html = html.fromstring("<html></html>")
