import time
from datetime import date

from dateutil.rrule import MONTHLY, rrule
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
        self.url = "https://www.cadc.uscourts.gov/internet/opinions.nsf/OpinionsByMonday?OpenView&StartKey=20151020150928&Count=2&scode=1"
        self.court_id = self.__module__
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                MONTHLY,
                dtstart=date(1997, 9, 1),
                until=date(2015, 1, 1),
            )
        ]

    @override
    def _get_case_names(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            "//div[@class='row-entry'][position() mod 2 = 1]/span[2]/text()"
        )
        return texts

    @override
    def _get_download_urls(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(
            "//div[@class='row-entry'][position() mod 2 = 1]/span[1]/a/@href"
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
            "//div[@class='row-entry'][position() mod 2 = 0]/span[2]/text()"
        )
        for date_string in date_strings:
            dates.append(
                date.fromtimestamp(
                    time.mktime(time.strptime(date_string, "%m/%d/%Y"))
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
            "//div[@class='row-entry'][position() mod 2 = 1]/span[1]/a/text()"
        )
        return texts

    @override
    def _get_precedential_statuses(self) -> list[str]:
        return ["Published" for _ in range(0, len(self))]

    @override
    async def _download_backwards(self, d: date) -> None:
        self.url = "https://www.cadc.uscourts.gov/internet/opinions.nsf/OpinionsByRDate?OpenView&count=100&SKey={}".format(
            d.strftime("%Y%m")
        )

        self.html = await self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
