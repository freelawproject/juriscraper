"""Scraper for North Carolina Supreme Court
CourtID: nc
Court Short Name: N.C.
Reviewer:
History:
    2014-05-01: Created by Brian Carver
    2014-08-04: Rewritten by Jon Andersen with complete backscraper
    2025-04-22: grossir, Update to OpinionSiteLinear
"""

import re
from datetime import datetime

from lxml import html
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import BackscrapeOptions
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[int]):
    start_year = 1998
    current_year = datetime.today().year
    court = "sc"
    court_number = 1
    row_xpath = "//span[span[@class='title']] | //td[span[@class='title']]"
    date_xpath = "../../preceding-sibling::tr//strong[contains(text()[1], 'Filed:')] | ../preceding-sibling::tr/td[contains(text(), 'Rule 30e')]"
    date_regex = r"Filed: (?P<date>[\d\w ]+)"
    coa_rgx = re.compile(
        r"(?P<date>\d[\d \w]+)[\t\xa0\n]+- Rule 30e", flags=re.M
    )
    pattern = r"(?P<name>.*?)(?:[\s,]+\s*(?P<cite>\d+\s+NC(?:\s+App)?\s+\d+))?\s*\(\s*(?P<docket>[^\s]+)\s*-\s*(?P<status>[^)]+)\s*\)"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.base_url = (
            "https://appellate.nccourts.org/opinion-filings/?c={}&year={}"
        )
        self.url = self.base_url.format(self.court, self.current_year)
        self.make_backscrape_iterable(kwargs)

    @override
    def _process_html(self) -> None:
        """Process the html

        :return: None
        """
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(self.row_xpath)
        for row in rows:
            title = row.find("span[@class='title']")
            title = title.text_content() if title is not None else ""
            links: list[str] = row.xpath("span[@class='title']/@onclick")
            summary = row.find("span[@class='desc']")
            summary = summary.text_content() if summary is not None else ""
            if not bool(links):
                logger.warning("No link for row %s", title)
                continue
            url = links[0][13:-2].replace("http:", "https:")
            m = re.search(self.pattern, title)
            if m is None:
                raise ValueError(f"Could not parse opinion title: {title!r}")
            name, citation, docket, status = m.groups()
            author = row.find("span[@class='author']/i")
            author = (
                author.text_content().strip() if author is not None else ""
            )
            per_curiam = author == "Per Curiam"
            date = self.extract_date(row)
            self.cases.append(
                {
                    "per_curiam": per_curiam,
                    "author": author if not per_curiam else "",
                    "docket": docket,
                    "status": status,
                    "name": name,
                    "url": url,
                    "date": date,
                    "summary": summary,
                    "citation": (citation if bool(citation) else ""),
                }
            )

    def extract_date(self, row: html.HtmlElement) -> str:
        """Extract date str for opinion in row

        :param row: row to process
        :return: date string
        """
        date_block: str = row.xpath(self.date_xpath)[-1].text_content()
        if (match := re.search(self.date_regex, date_block)) is not None:
            return match.group("date")
        # Second pattern for ncctapp unpublished opinions
        match = self.coa_rgx.search(date_block)
        if match is None:
            raise ValueError(f"Could not parse opinion date: {date_block!r}")
        return match.group("date")

    @override
    async def _download_backwards(self, year: int) -> None:
        """Build year URL and scrape

        :param year: year to scrape
        :return None
        """
        self.url = self.base_url.format(self.court, year)
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
