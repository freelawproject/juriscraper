"""Scraper for the Air Force Court of Criminal Appeals
CourtID: afcca
Court Short Name: Air Force Court of Criminal Appeals
Reviewer: mlr
History:
    15 Sep 2014: Created by Jon Andersen
"""

from datetime import date

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import BackscrapeOptions
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[int]):
    base_url = "http://afcca.law.af.mil/content/opinions_date_{}.html"
    start_year = 2002

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        kwargs.setdefault("verify", False)
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.current_year = date.today().year
        self.make_backscrape_iterable(kwargs)
        self.url = self.base_url.format(self.current_year)

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(
            ".//img[contains(@src, 'pdf.gif')]/../.."
        )[:-1]
        for row in rows:
            status = row.findall(".//td")[3].text_content()
            if status != "Published":
                status = "Unpublished"
            self.cases.append(
                {
                    "url": row.xpath(".//td/a/@href")[0],
                    "docket": row.findall(".//td")[2].text_content(),
                    "name": row.xpath(".//td/a")[0].text_content(),
                    "date": row.findall(".//td")[4].text_content(),
                    "status": status,
                }
            )

    @override
    async def _download_backwards(self, year: int) -> None:
        """Build URL with year input and scrape

        :param year: year to scrape
        :return None
        """
        self.url = self.base_url.format(year)
        self.html = await self._download()
        self._process_html()

    @override
    def make_backscrape_iterable(self, kwargs: BackscrapeOptions) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        start = int(start) if bool(start) else self.start_year
        end = int(end) + 1 if bool(end) else self.current_year

        self.back_scrape_iterable = range(start, end)
