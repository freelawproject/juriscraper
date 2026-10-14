# Author: Michael Lissner
# Date created: 2013-06-06

import re
from collections.abc import Sequence
from datetime import date, datetime

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.state import nd


class Site(nd.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date] | date]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        self.crawl_date = today
        self.url = "http://www.ndcourts.gov/opinions/month/%s.htm" % (
            today.strftime("%b%Y")
        )

    @override
    async def _get_download_urls(self) -> list[str]:
        """We use a fetcher and a DeferringList object and a HEAD request
        to test whether the wpd exists for a case"""

        async def fetcher(html_link: str) -> str:
            if self.test_mode_enabled():
                return html_link  # Can't fetch remote during tests
            match = re.search(r"(\d+)", html_link)
            if match is None:
                raise ValueError(f"Missing case number in {html_link!r}")
            case_number = match.group(0)
            wpd_link = f"http://www.ndcourts.gov/wp/{case_number}.wpd"
            r = await self.request["session"].head(
                wpd_link,
                follow_redirects=False,
                headers={"User-Agent": self.user_agent},
            )
            if r.status_code == 200:
                return wpd_link
            else:
                return html_link

        if self.crawl_date >= date(1998, 10, 1):
            path = '//a/@href[contains(., "/court/opinions/")]'
        else:
            path = "//ul//a[text()]/@href"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        seed: list[str] = self.html.xpath(path)
        case_names = []
        for case in seed:
            case_names.append(await fetcher(case))
        return case_names

    @override
    def _get_case_names(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        if self.crawl_date >= date(1998, 10, 1):
            path = '//a[contains(@href, "/court/opinions/")]/text()'
            texts: list[str] = self.html.xpath(path)
            return texts
        else:
            path = "//ul//a/text()"
            names: list[str] = self.html.xpath(path)
            case_names = []
            if self.crawl_date < date(1996, 11, 1):
                # A bad time.
                for name in names:
                    name = name.rsplit("-")[0]
                    case_names.append(name)
                return case_names
            else:
                return list(names)

    @override
    def _get_case_dates(self) -> list[date | None]:
        # A tricky one. We get the case dates, but each can have different number of cases below it, so we have to
        # count them.
        case_dates: list[date | None] = []
        dt: date | None = None
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        if self.crawl_date >= date(1998, 10, 1):
            test_path = "//body/a"
            if len(self.html.xpath(test_path)) == 0:
                # It's a month with no cases (like Jan, 2009)
                return []
            path = "//body/a|//body/font"
            elements: list[HtmlElement] = self.html.xpath(path)
            for e in elements:
                if e.tag == "font":
                    date_str = e.text_content()
                    dt = datetime.strptime(date_str, "%B %d, %Y").date()
                elif e.tag == "a":
                    if dt is not None:
                        case_dates.append(dt)
        else:
            path = "//h4|//li"
            matches: list[HtmlElement] = self.html.xpath(path)
            for e in matches:
                if e.tag == "h4":
                    # We make dates on h4's because there's one h4 per date.
                    date_str = e.text_content().strip()
                    dt = datetime.strptime(date_str, "%B %d, %Y").date()
                elif e.tag == "li":
                    if dt is not None:
                        # We append on li's, because there's one li per case.
                        case_dates.append(dt)
        return case_dates

    @override
    def _get_precedential_statuses(self) -> list[str]:
        return ["Published"] * len(self)

    @override
    def _get_docket_numbers(self) -> list[str]:
        if self.crawl_date >= date(1998, 10, 1):
            path = '//a/@href[contains(., "/court/opinions/")]'
        else:
            path = "//ul//a[text()]/@href"
        docket_numbers = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        html_links: list[str] = self.html.xpath(path)
        for html_link in html_links:
            if (match := re.search(r"(\d+)", html_link)) is not None:
                docket_numbers.append(match.group(0))
        return docket_numbers

    @override
    def _get_citations(self) -> list[str] | None:
        if self.crawl_date < date(1997, 2, 1):
            # Old format, but no neutral cites, thus short circuit the function.
            return None
        elif self.crawl_date < date(1998, 10, 1):
            # Old format with: 1997 ND 30 - Civil No. 960157 or 1997 ND 30
            path = "//li/text()"
        else:
            # New format with: 1997 ND 30
            path = "//body/text()"
        neutral_cites = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(path)
        for t in texts:
            if (
                match := re.search(
                    r"^.{0,5}(\d{4} ND (?:App )?\d{1,4})", t, re.MULTILINE
                )
            ) is not None:
                neutral_cites.append(match.group(1))
        return neutral_cites

    @override
    def _post_parse(self) -> None:
        # Remove any information that applies to non-appellate cases.
        if not bool(self.citations):
            return
        delete_items = {
            i
            for i, citation in enumerate(self.citations)
            if (bool(citation) and "App" in citation)
        }
        for attr in self._all_attrs:
            values: Sequence[object] | None = getattr(self, attr)
            if values is not None:
                setattr(
                    self,
                    attr,
                    [
                        value
                        for i, value in enumerate(values)
                        if i not in delete_items
                    ],
                )

    @override
    async def _download_backwards(
        self, dates: tuple[date, date] | date
    ) -> None:
        if not isinstance(dates, date):
            raise TypeError("Expected a month to backfill")
        self.crawl_date = dates
        self.url = "http://www.ndcourts.gov/opinions/month/%s.htm" % (
            dates.strftime("%b%Y")
        )
        self.html = await self._download()
