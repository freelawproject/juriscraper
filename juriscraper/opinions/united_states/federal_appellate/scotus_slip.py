"""
Court Contact: https://www.supremecourt.gov/contact/contact_webmaster.aspx
"""

import re
from datetime import date, datetime

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import BackscrapeOptions
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[str]):
    justices = {
        "A": "Samuel Alito",
        "AB": "Amy Coney Barrett",
        "AS": "Antonin Scalia",
        "B": "Stephen Breyer",
        "BK": "Brett Kavanaugh",
        "D": "Decree",
        "DS": "David Souter",
        "EK": "Elana Kagan",
        "G": "Ruth Bader Ginsburg",
        "JS": "John Paul Stephens",
        "K": "Anthony Kennedy",
        "KJ": "Ketanji Brown Jackson",
        "NG": "Neil Gorsuch",
        "PC": "Per Curiam",
        "R": "John G. Roberts",
        "SS": "Sonia Sotomayor",
        "T": "Clarence Thomas",
    }
    base_url = "https://www.supremecourt.gov/opinions/slipopinion"
    first_opinion_date = datetime(2018, 6, 25)
    days_interval = 365

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[str]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = f"{self.base_url}/{self.get_term()}"
        self.make_backscrape_iterable(kwargs)
        self.should_have_results = True

    @staticmethod
    def get_term(
        date_of_interest: date | datetime | None = None,
    ) -> int:
        """The URLs for SCOTUS correspond to the term, not the calendar.

        The terms kick off on the first Monday of October, so we use October 1st
        as our cut off date.
        """
        if date_of_interest is None:
            date_of_interest = date.today()
        term_cutoff = date(date_of_interest.year, 10, 1)
        if isinstance(date_of_interest, datetime):
            date_of_interest = date_of_interest.date()
        year = int(date_of_interest.strftime("%y"))
        # Return the previous year if we haven't reached the cutoff
        return year - 1 if date_of_interest < term_cutoff else year

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//tr")
        for row in rows:
            cells = row.findall(".//td")
            if len(cells) != 6:
                continue
            _, date, docket, link, justice, citation = row.findall(".//td")
            if not bool(link.text_content()):
                continue
            name = link.find(".//a")
            self.cases.append(
                {
                    "citation": self.clean_citation(citation.text_content()),
                    "date": date.text_content(),
                    "url": link.xpath(".//a/@href")[0],
                    "name": name.text_content() if name is not None else "",
                    "docket": docket.text_content(),
                    "judge": self.justices[justice.text_content()],
                }
            )

    @staticmethod
    def clean_citation(citation: str) -> str:
        """Return the citation if it is "volume U.S. page", or "" otherwise

        Until an opinion is paginated, the citation column only shows its
        volume and part, such as "609/2".

        :param citation: the text of the citation column
        :return: the citation, or an empty string
        """
        if (
            re.fullmatch(r"\d+\s*U\.\s*S\.?\s*\d+", citation.strip())
            is not None
        ):
            return citation.strip()
        return ""

    @override
    def make_backscrape_iterable(self, kwargs: BackscrapeOptions) -> None:
        """Use the default make_backscrape_iterable to parse input
        and create date objects. Then, use the dates to get the terms

        Note that the HTML slipopinion page exists only since term 17

        :return: a list of URLs
        """
        date_ranges = self._get_backscrape_date_ranges(kwargs)
        if not bool(date_ranges):
            self.back_scrape_iterable = []
            return
        start = self.get_term(date_ranges[0][0])
        end = self.get_term(date_ranges[-1][1])
        if start == end:
            self.back_scrape_iterable = [f"{self.base_url}/{start}"]
        else:
            self.back_scrape_iterable = [
                f"{self.base_url}/{yy}" for yy in range(start, end)
            ]

    @override
    async def _download_backwards(self, d: str) -> None:
        self.url = f"{self.base_url}/{d}"
        logger.info("Backscraping %s", self.url)
        self.html = await self._download()
        self._process_html()
