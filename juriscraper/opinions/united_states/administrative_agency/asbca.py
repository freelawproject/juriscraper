"""Scraper for Armed Services Board of Contract Appeals
CourtID: asbca
Court Short Name: ASBCA
Author: Jon Andersen
Reviewer: mlr
History:
    2014-09-11: Created by Jon Andersen
    2016-03-17: Website and phone are dead. Scraper disabled in __init__.py.
"""

from datetime import datetime
from urllib.parse import urljoin

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.asbca.mil/"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.year = str(datetime.today().year)
        self.url = urljoin(self.base_url, f"Decisions/{self.year}/")
        self.status = "Published"
        # Outdated headers may cause 403 responses. See #1693
        self.request["headers"] = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=0, i",
            "sec-ch-ua": self.chrome_sec_ch_ua,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-site": "cross-site",
            "upgrade-insecure-requests": "1",
            "user-agent": self.chrome_user_agent,
        }
        self.needs_special_headers = True

    @override
    def _process_html(self) -> None:
        # Exclude headers and rows that only have the month name
        if self.test_mode_enabled():
            self.year = "2026"

        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(
            "//tr[not(th) and not(.//span[@style='background-color:#F8C100;']) and descendant::a]"
        )
        for row in rows:
            if len(row.findall(".//td")) != 4:
                logger.warning(
                    "Row does not have expected number of cells %s",
                    row.text_content().strip(),
                )
                continue

            url: str = row.xpath(".//a/@href")[0]
            date, docket, name, judge = (
                cell.text_content().strip() for cell in row.findall(".//td")
            )

            if self.year not in date:
                # site returns all records in a single request
                # in a normal scrape, check only the most recent year
                break

            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "url": url,
                    "docket": docket,
                    "judge": judge,
                }
            )
