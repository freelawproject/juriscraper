"""
Scraper for the Supreme Court of Tennessee, Workers Compensation Panel
CourtID: tenn
Court Short Name: Tenn.
"""

import re
from datetime import date, datetime
from urllib.parse import urlencode

from httpx import HTTPError
from lxml.html import HtmlElement
from typing_extensions import override

from juriscraper.AbstractSite import logger
from juriscraper.opinions.united_states.state import tenn
from juriscraper.OpinionSite import OpinionSite


class Site(tenn.Site):
    first_opinion_date = datetime(1996, 3, 14)
    days_interval = 30
    base_url = "https://www.tncourts.gov/courts/work-comp/opinions"
    # A 30 day window has needed at most 2 pages; this only stops a
    # backscrape that would otherwise never end
    max_pages = 20

    extract_from_text = OpinionSite.extract_from_text

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = self.base_url
        self.section_selector = (
            "views-field views-field-field-opinions-case-brief"
        )

        # The docket is the first floating text after the case name link.
        # Older dockets have no "WC" in them, e.g. 01S01-9509-CV-00147
        # A judge line ("Authoring Judge: ...") is never taken as the docket
        self.docket_xpath = (
            "text()[normalize-space()][1][not(contains(., ':'))]"
        )

    @override
    def _process_html(self) -> None:
        """Drop rows that have no opinion before parsing

        Some older rows are empty: no link, docket or summary
        """
        if self.html is None:
            return
        for section in self.html.xpath(
            f"//td[contains(@class, '{self.section_selector}')][not(.//a)]"
        ):
            row = section.getparent()
            logger.info("Skipping a row with no opinion link")
            row.getparent().remove(row)
        super()._process_html()

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Download every page of results for a date range

        This page filters on `field_opinions_date_filed_value` and
        `field_opinions_date_filed_value_1`, unlike the Supreme Court page,
        and some months have more than one page of results

        Pagination stops when a page has no "next" link, when a page links
        the same opinions as the page before it, or after `max_pages`. If a
        later page fails to download, the pages already parsed are kept

        :param dates: (start, end) dates of the range to download
        :return: None
        """
        start, end = dates
        previous_links: set[str] = set()
        for page in range(self.max_pages):
            params = {
                "field_opinions_date_filed_value": start.strftime("%Y-%m-%d"),
                "field_opinions_date_filed_value_1": end.strftime("%Y-%m-%d"),
                "page": page,
            }
            self.url = f"{self.base_url}?{urlencode(params)}"
            logger.info("Backscraping %s", self.url)
            try:
                self.html = await self._download()
            except HTTPError:
                if page == 0:
                    raise
                logger.warning(
                    "Download failed for %s; keeping the %s earlier pages",
                    self.url,
                    page,
                )
                return

            # Compare links, not parsed cases: tenn merges rows of the same
            # case, so a new page can legitimately add no new case
            links = set(
                self.html.xpath(
                    f"//td[contains(@class, '{self.section_selector}')]//a/@href"
                )
            )
            if page and links == previous_links:
                logger.warning(
                    "%s repeats the previous page; stopping", self.url
                )
                return
            previous_links = links

            self._process_html()
            if self.html is None or not self.html.xpath(
                "//li[contains(@class, 'pager__item--next')]"
            ):
                return

        logger.warning(
            "Stopped after %s pages for %s to %s", self.max_pages, start, end
        )

    def get_summary(self, section: HtmlElement) -> str:
        """Get the summary considering some XPath variations

        :param section: the html element containing the case summary
        :return the parsed summary, or an empty string
        """
        try:
            return super().get_summary(section)
        except IndexError:
            pass

        # last non empty floating text in the section
        summary = section.xpath("text()[normalize-space()]")[-1]
        # ensure we didn't pick up a judge field
        if " Judge:" not in summary:
            return summary

        # sometimes each line of the summary is inside a div
        # See 2022 case 'Sonney Summers v. RTR Transportation Services et al.'
        if containers := section.xpath("div/text()"):
            return re.sub(r"\s+", " ", " ".join(containers))

        return ""
