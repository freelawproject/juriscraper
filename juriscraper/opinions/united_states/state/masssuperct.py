"""
Scraper for Massachusetts Superior Court
CourtID: masssuperct
Court Short Name: MS
Author: Luis Manzur
Court Contact: SJCReporter@sjc.state.ma.us (617) 557-1030
Date: 2025-07-16
History:
    - Created by luism
    - 2026-03-25: Switched from JSON API to HTML page scraping
Notes:
    Cloudflare blocks GET requests via TLS fingerprinting.
    We use POST with an empty body to bypass this.
"""

from datetime import date, datetime
from urllib.parse import quote, urljoin

from lxml import etree, html
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.exceptions import InvalidDocumentError
from juriscraper.lib.html_utils import strip_bad_html_tags_insecure
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.lib.type_utils import BackscrapeOptions
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

logger = make_default_logger()


class Site(OpinionSiteLinear[date]):
    court_name = "Superior Court"
    first_opinion_date = datetime(2017, 6, 20)
    use_urllib = True
    base_url = "https://www.socialaw.com/services/slip-opinions/"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[date]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.search_date = date.today()
        self.url = self._build_url()
        self.method = "POST"
        self.parameters = {}
        self.status = "Published"
        self.expected_content_types = ["text/html"]
        self.days_interval = 30
        self.make_backscrape_iterable(kwargs)

    def _build_url(self) -> str:
        """Build the listing URL with court and month query parameters.

        :return: Full URL with encoded query parameters
        """
        month_str = quote(self.search_date.strftime("%B %Y"))
        court_str = quote(self.court_name)
        return f"{self.base_url}?Court={court_str}&Month={month_str}"

    @override
    def _process_html(self) -> None:
        """Parse opinion listing from HTML accordion items.

        :return: None
        """
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        items: list[HtmlElement] = self.html.xpath(
            "//div[contains(@class, 'slip-opinions-list')]"
            "//div[@class='accordion-item']"
        )
        for item in items:
            names: list[str] = item.xpath(
                ".//strong[contains(@class, 'title')]//text()"
            )
            name = names[0].strip() if bool(names) else ""

            dates: list[str] = item.xpath(
                ".//div[contains(@class, 'dates-section')]"
                "//div[@class='rich-text rich-text-sm']//text()"
            )
            date_str = dates[0].strip() if bool(dates) else ""

            dockets: list[str] = item.xpath(
                ".//div[contains(@class, 'docket-section')]"
                "//div[@class='section-header']"
                "//div[@class='rich-text rich-text-sm']//text()"
            )
            docket = dockets[0].strip() if bool(dockets) else ""

            urls: list[str] = item.xpath(
                ".//div[contains(@class, 'docket-section')]"
                "//a[contains(@class, 'btn')]/@href"
            )
            url = (
                urljoin("https://www.socialaw.com", urls[0])
                if bool(urls)
                else ""
            )

            if not bool(name) or not bool(url):
                logger.warning(
                    "masssuperct: missing name or URL for docket '%s', skipping",
                    docket,
                )
                continue

            self.cases.append(
                {
                    "name": titlecase(name),
                    "date": date_str,
                    "url": url,
                    "docket": docket,
                }
            )

    @override
    @staticmethod
    def cleanup_content(content: bytes) -> bytes:
        """Remove non-opinion HTML

        Cleanup HTML from Social Law page so we can properly display
        the content.

        :param content: The scraped HTML
        :return: Cleaner HTML
        """
        text = content.decode("utf-8")
        tree = strip_bad_html_tags_insecure(text, remove_scripts=True)
        elements: list[HtmlElement] = tree.xpath(
            "//div[contains(@class, 'primary-content-rich-text')]"
        )

        if not bool(elements):
            elements: list[HtmlElement] = tree.xpath(
                "//div[contains(@class, 'primary-content-body')]"
            )
        if not bool(elements):
            raise InvalidDocumentError(
                "masssuperct: no opinion content found in page"
            )

        new_tree = html.Element("html")
        body = etree.SubElement(new_tree, "body")
        body.append(elements[0])
        return html.tostring(new_tree)

    @override
    async def _download_backwards(self, search_date: date) -> None:
        """Download and process HTML for a given target date.

        :param search_date: The date for which to download and process
            opinions.
        :return: None
        """
        self.search_date = search_date
        self.url = self._build_url()
        self.html = await self._download()
        self._process_html()

    @override
    def make_backscrape_iterable(self, kwargs: BackscrapeOptions) -> None:
        """Make back scrape iterable

        :param kwargs: the back scraping params
        :return: None
        """
        date_ranges = self._get_backscrape_date_ranges(kwargs)
        if not bool(date_ranges):
            self.back_scrape_iterable = []
            return
        self.back_scrape_iterable = unique_year_month(date_ranges)
