"""
Scraper for the United States Bankruptcy Appellate Panel for the Tenth Circuit
CourtID: bap10
Court Short Name: 10th Cir. BAP
Auth: Jon Andersen <janderse@gmail.com>
Reviewer: mlr
History:
    2014-09-01: First draft by Jon Andersen
    2014-09-02: Revised by mlr to use _clean_text() instead of pushing logic
                into the _get_case_dates function.
    2025-08-28, lmanzur: Retrieve lower_court.
"""

from datetime import date, datetime, timedelta
from urllib.parse import urlencode

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[tuple[date, date]]):
    base_url = url = "https://www.bap10.uscourts.gov/opinion/search/results"
    first_opinion_date = datetime(1996, 11, 12)
    days_interval = 120

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.set_url()
        self.make_backscrape_iterable(kwargs)

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        for row in self.html.findall(".//tr"):
            if not bool(row.findall(".//td")):
                continue
            self.cases.append(
                {
                    "docket": row.findall(".//td")[0].text_content().strip(),
                    "name": row.findall(".//td")[1].text_content().strip(),
                    "date": row.findall(".//td")[2].text_content().strip(),
                    "lower_court": row.findall(".//td")[3]
                    .text_content()
                    .strip(),
                    "url": row.xpath(".//a/@href")[0],
                    "status": "Published",
                }
            )

    def set_url(
        self, start: date | None = None, end: date | None = None
    ) -> None:
        """Sets URL with date filters in query string

        :param start: optional start date
        :param end: optional end date
        :return None:
        """
        if end is None:
            end = date.today()
        if start is None:
            start = end - timedelta(30)

        params = {
            "keywords": "",
            "parties": "",
            "judges": "",
            "field_opinion_date_value[min][date]": start.strftime("%m/%d/%Y"),
            "field_opinion_date_value[max][date]": end.strftime("%m/%d/%Y"),
            "exclude": "",
        }
        self.url = f"{self.base_url}?{urlencode(params)}"

    @override
    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.set_url(*dates)
        self.html = await self._download()
        self._process_html()
