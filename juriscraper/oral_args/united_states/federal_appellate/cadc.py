"""Scraper for D.C. Circuit of Appeals
CourtID: cadc
Court Short Name: cadc
Author: Andrei Chelaru
Reviewer: mlr
Date created: 18 July 2014
Updated: 2024-10-10
"""

from datetime import date, datetime
from urllib.parse import urljoin

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import BackscrapeOptions
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear[date]):
    days_interval = 28  # ensure monthly backscraper ticks
    first_opinion_date = datetime(2007, 9, 10)
    base_url = "https://media.cadc.uscourts.gov/recordings/bydate/{}"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[date]],
    ) -> None:
        kwargs.setdefault("verify", False)
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        self.url = self.base_url.format(today.strftime("%Y/%-m"))
        self.make_backscrape_iterable(kwargs)

    @override
    def _process_html(self) -> None:
        anchor_xpath = "a[contains(@href, '/recordings/docs/') and contains(@href, '.mp3')]"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(
            f"//div[div[div[div[{anchor_xpath}]]]]"
        )
        for row in rows:
            ahref: list[HtmlElement] = row.xpath(f".//{anchor_xpath}")
            url = ahref[0].attrib["href"]
            docket: str = ahref[0].xpath("text()")[0]

            if "mp3" not in url:
                logger.info("Not a mp3 URL? %s", url)
                continue

            cells = row.findall("div[2]/div")

            # From: "Judges: Tatel, Griffith, Sentelle"
            # To: "Tatel; Griffith; Sentelle"
            judges = (
                cells[1].text_content().split(": ", 1)[-1].replace(",", ";")
            )
            self.cases.append(
                {
                    "url": urljoin(self.base_url, url),
                    "docket": docket,
                    "name": cells[0].text_content(),
                    "judge": judges,
                    "attorney": cells[2].text_content(),
                    "date": cells[3].text_content(),
                }
            )

    @override
    async def _download_backwards(self, target_date: date) -> None:
        """Download historical data

        Note that this URL will work:
        "https://media.cadc.uscourts.gov/recordings/bydate/2007/9"
        but this won't
        "https://media.cadc.uscourts.gov/recordings/bydate/2007/09"

        That's why the '%-m' formatter is needed
        """
        self.url = self.base_url.format(target_date.strftime("%Y/%-m"))
        logger.info("Backscraping URL '%s'", self.url)
        self.html = await self._download()
        self._process_html()

    @override
    def make_backscrape_iterable(self, kwargs: BackscrapeOptions) -> None:
        """Use base function to generate a range, then pick
        unique year-month combinations to build the backscrape
        URLS
        """
        date_ranges = self._get_backscrape_date_ranges(kwargs)
        if not bool(date_ranges):
            self.back_scrape_iterable = []
            return
        self.back_scrape_iterable = unique_year_month(date_ranges)
