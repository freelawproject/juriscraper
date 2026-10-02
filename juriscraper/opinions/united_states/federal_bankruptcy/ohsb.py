"""
Scraper for the United States Bankruptcy Court Southern District of Ohio
CourtID: ohsb
Court Short Name: Bankr. S.D. Ohio
Author: Heron Fonsaca
Reviewer: -
History:
 - 2026-10-02, heronfonsaca: created
"""

import re
from datetime import date
from typing import Literal

from lxml import html
from lxml.html import HtmlElement

from juriscraper.lib.exceptions import logger
from juriscraper.lib.string_utils import convert_date_string, clean_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    base_url = "https://www.ohsb.uscourts.gov/judges-information/opinions"
    title_regex = re.compile(r"^(?P<name>.*?)\s*\((?P<docket>[^()]*)\)\s*$")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.base_url
        # Complete this variable if you create a backscraper.
        self.back_scrape_iterable = None
        self.should_have_results = True

    def _get_download_urls(self) -> list[str]:
        return list(self.html.xpath(f"//tr/td[3]/a/@href"))

    def _get_case_names(self) -> list[str]:
        case_names = []
        for e in self.html.xpath("//tr/td[2]"):
            case_names.append(self._extract_from_title(e, "name"))
        return case_names

    def _get_case_dates(self) -> list[date | None]:
        case_dates = []
        for date_string in self.html.xpath("//tr/td[1]/span/text()"):
            case_dates.append(convert_date_string(date_string, datetime=False))
        return case_dates

    def _get_precedential_statuses(self) -> list[str]:
        statuses = []
        for e in self.html.xpath("//tr/td[3]/a"):
            s = html.tostring(e, method="text", encoding="unicode")
            if "Opinion" in s:
                statuses.append("Published")
            elif "Nonprecedential" in s:
                statuses.append("Unpublished")
            # elif "Memorandum" in s:
            #     statuses.append("Memorandum")
            # elif "Order" in s:
            #     statuses.append("Order")
            else:
                statuses.append("Unknown")
        return statuses

    def _get_docket_numbers(self) -> list[str]:
        docket_numbers = []
        for e in self.html.xpath("//tr/td[2]"):
            docket_numbers.append(self._extract_from_title(e, "docket"))
        return docket_numbers

    def _get_citations(self) -> list[str]:
        neutral_citations = []
        for e in self.html.xpath("//tr/td[2]"):
            docket_number = self._extract_from_title(e, "docket")
            year, item_number = docket_number.split("-")
            neutral_citation = f"20{year} OHSBK {item_number}"
            neutral_citations.append(neutral_citation)
        return neutral_citations

    def _get_summaries(self) -> list[str]:
        return list(self.html.xpath(f"//tr/td[3]/a/text()"))

    def _get_adversary_numbers(self):
        """
        Similar to a docket number, but found only in bankruptcy cases.
        """
        return None

    def _extract_from_title(
        self, element: HtmlElement, attribute: Literal["name", "docket"]
    ) -> str:
        """Extract case name or docket number from opinion title.

        For example, the following title:
           'In re Jennifer Lee Hernandez (26-30232)'

        Result in values:
           name = 'In re Jennifer Lee Hernandez' and docket = '26-30232'
        """
        title = html.tostring(element, method="text", encoding="unicode")
        title = clean_string(title)

        title_match = self.title_regex.search(title)
        if not title_match:
            logger.warning(
                "%s: could not parse title '%s'", self.court_id, title
            )
            return ""

        return title_match.group(attribute)

    async def _download_backwards(self, date_str):
        """
        This is a simple method that can be used to generate Site objects
        that can be used to paginate through a court's entire website.

        This method is usually called by a backscraper caller (see the
        one in CourtListener/alert/scrapers for details), and typically
        modifies aspects of the Site object's attributes such as Site.url.

        A simple example has been provided below. The idea is that the
        caller runs this method with a different variable on each iteration.
        That variable is often a date that is getting iterated or is simply
        a index (i), that we iterate upon.

        This can also be used to hold notes useful to future backscraper
        development.
        """
        self.url = f"http://example.com/new/url/{date_str}"
        self.html = await self._download()
