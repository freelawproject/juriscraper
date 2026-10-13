#  Scraper for Fourth Circuit of Appeals
# CourtID: ca4
# Court Short Name: ca4
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 18 July 2014

from datetime import date

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, convert_date_string
from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.ca4.uscourts.gov/oral-argument/listen-to-oral-arguments"

    @override
    def _get_download_urls(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath("//tr/td[2]//a/@href")
        return texts

    @override
    def _get_case_names(self) -> list[str]:
        return self.text_from_cell(3)

    @override
    def _get_case_dates(self) -> list[date | None]:
        return [convert_date_string(date) for date in self.text_from_cell(1)]

    @override
    def _get_judges(self) -> list[str]:
        return self.text_from_cell(4)

    @override
    def _get_docket_numbers(self) -> list[str]:
        return self.text_from_cell(2)

    def text_from_cell(self, cell_number: int) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        cells: list[HtmlElement] = self.html.xpath("//tr/td[%d]" % cell_number)
        return [cell.text_content().strip() for cell in cells]
