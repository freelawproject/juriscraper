import time
from datetime import date

from dateutil.rrule import DAILY, rrule
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite[date]):
    status: int

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[date]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        today = date.today()
        self.url = "http://www.ca10.uscourts.gov/opinion/search/results?query=%20date%3A{}".format(
            today.strftime("%m/%d/%Y")
        )
        self.court_id = self.__module__
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                DAILY,
                dtstart=date(1995, 11, 1),
                until=date(2015, 1, 1),
            )
        ]
        self.base = (
            "//table[contains(concat('', @class, ''), 'search-results')]//tr"
        )

    @override
    def _get_case_names(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            f"{self.base}/td[@class='case-name']/text()"
        )
        return texts

    @override
    def _get_download_urls(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            f"{self.base}/td[@class='link']/a/@href"
        )
        return texts

    @override
    def _get_case_dates(self) -> list[date]:
        dates = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        date_strings: list[str] = self.html.xpath(
            f"{self.base}/td[@class='publish-date']/text()"
        )
        for date_string in date_strings:
            # ex: Nov-02-1995
            dates.append(
                date.fromtimestamp(
                    time.mktime(time.strptime(date_string, "%b-%d-%Y"))
                )
            )
        return dates

    @override
    def _get_docket_numbers(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            f"{self.base}/td[@class='case-no']/text()"
        )
        return texts

    @override
    def _get_precedential_statuses(self) -> list[str]:
        return ["Published"] * len(self)

    @override
    def _get_lower_courts(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            f"{self.base}/td[@class='origin']/text()"
        )
        return texts

    @override
    async def _download_backwards(self, d: date) -> None:
        self.url = "http://www.ca10.uscourts.gov/opinion/search/results?query=%20date%3A{}".format(
            d.strftime("%m/%d/%Y")
        )

        self.html = await self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
