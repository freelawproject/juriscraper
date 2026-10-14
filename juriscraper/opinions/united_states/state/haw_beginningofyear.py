# Auth: mlr
# Date: 2013-05-28

from datetime import date

from lxml import html
from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import haw


class Site(haw.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[date]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__

        # If it's the beginning of January, we need to make sure that we aren't
        # missing any late-coming cases from the previous year.
        today = date.today()
        if today.day < 15 and today.month == 1:
            year = today.year - 1
            self.url = (
                "http://www.courts.state.hi.us/opinions_and_orders/opinions/%s/index.html"
                % year
            )
        else:
            # This simply aborts the crawler.
            self.html = html.fromstring("<html></html>")
