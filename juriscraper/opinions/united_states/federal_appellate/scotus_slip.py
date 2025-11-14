"""
Court Contact: https://www.supremecourt.gov/contact/contact_webmaster.aspx
"""

from datetime import date, datetime
from typing import Optional, Union
from urllib.parse import urljoin

from lxml.html import HtmlElement

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import normalize_dashes
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
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

    first_opinion_date = datetime(2018, 6, 25)
    days_interval = 365

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.court = "slipopinion"
        self.base_url = "https://www.supremecourt.gov/opinions/"
        self.make_backscrape_iterable(kwargs)
        self.should_have_results = True
        self.url = urljoin(self.base_url, f"{self.court}/{self.get_term()}")

    @staticmethod
    def get_term(
        date_of_interest: Union[date, datetime, None] = None,
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

    def _process_html(self):
        for row in self.html.xpath("//tr"):
            cells = row.xpath(".//td")

            fields = self.get_fields(cells, row)
            if fields is None or fields[0] is None:
                logger.info("Skipping row: get_fields returned None")
                continue
            date, docket, link, revised, justice, citation = fields

            name = link.text_content()
            if not name:
                logger.info("Skipping row: empty name")
                continue
            name = name.split("Revisions:")[0].strip()
            hrefs = link.xpath(".//a/@href")
            if revised:
                revised_hrefs = revised.xpath(".//a/@href")
            else:
                revised_hrefs = []
            hrefs = hrefs + revised_hrefs
            for href in hrefs:
                self.cases.append(
                    {
                        "citation": citation.text_content(),
                        "date": date.text_content(),
                        "url": href,
                        "name": normalize_dashes(name),
                        "docket": docket.text_content(),
                        "judge": self.justices.get(justice.text_content()),
                    }
                )

    @staticmethod
    def get_fields(
        cells: list[HtmlElement], row: HtmlElement
    ) -> Optional[tuple[Optional[HtmlElement]]]:
        """
        Extract fields from a table row for slip opinions.

        :params cells: list of HtmlElement objects representing the row's cells
                row: HtmlElement for the table row to extract fields from
        :return: tuple(date, docket, link, revised, justice, citation) or None
        """
        if len(cells) != 6:
            return None
        _, date, docket, link, justice, citation = row.xpath(".//td")
        return date, docket, link, None, justice, citation

    def make_backscrape_iterable(self, kwargs: dict) -> list[str]:
        """Use the default make_backscrape_iterable to parse input
        and create date objects. Then, use the dates to get the terms

        Note that the HTML slipopinion page exists only since term 17

        :return: a list of URLs
        """
        super().make_backscrape_iterable(kwargs)
        start = self.get_term(self.back_scrape_iterable[0][0])
        end = self.get_term(self.back_scrape_iterable[-1][1])

        self.back_scrape_iterable = [yy for yy in range(start, end)]

    def _download_backwards(self, d: str):
        self.url = urljoin(self.base_url, f"{self.court}/{d}")
        logger.info("Backscraping %s", self.url)
        self.html = self._download()
        self._process_html()
