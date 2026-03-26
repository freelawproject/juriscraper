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

from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.html_utils import strip_bad_html_tags_insecure
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_name = "Superior Court"
    first_opinion_date = datetime(2017, 6, 20)
    use_urllib = True
    base_url = "https://www.socialaw.com/services/slip-opinions/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.search_date = datetime.today()
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

    def _process_html(self):
        """Parse opinion listing from HTML accordion items.

        :return: None
        """
        for item in self.html.xpath(
            "//div[contains(@class, 'slip-opinions-list')]"
            "//div[@class='accordion-item']"
        ):
            name = item.xpath(
                ".//strong[contains(@class, 'title')]//text()"
            )
            name = name[0].strip() if name else ""

            date_str = item.xpath(
                ".//div[contains(@class, 'dates-section')]"
                "//div[@class='rich-text rich-text-sm']//text()"
            )
            date_str = date_str[0].strip() if date_str else ""

            docket = item.xpath(
                ".//div[contains(@class, 'docket-section')]"
                "//div[@class='section-header']"
                "//div[@class='rich-text rich-text-sm']//text()"
            )
            docket = docket[0].strip() if docket else ""

            url = item.xpath(
                ".//div[contains(@class, 'docket-section')]"
                "//a[contains(@class, 'btn')]/@href"
            )
            url = (
                urljoin("https://www.socialaw.com", url[0]) if url else ""
            )

            if not name or not url:
                continue

            self.cases.append(
                {
                    "name": titlecase(name),
                    "date": date_str,
                    "url": url,
                    "docket": docket,
                }
            )

    @staticmethod
    def cleanup_content(content):
        """Remove non-opinion HTML

        Cleanup HTML from Social Law page so we can properly display
        the content.

        :param content: The scraped HTML
        :return: Cleaner HTML
        """
        content = content.decode("utf-8")
        tree = strip_bad_html_tags_insecure(content, remove_scripts=True)
        content = tree.xpath(
            "//div[contains(@class, 'primary-content-rich-text')]"
        )
        if not content:
            content = tree.xpath(
                "//div[contains(@class, 'primary-content-body')]"
            )
        if not content:
            return b""
        new_tree = etree.Element("html")
        body = etree.SubElement(new_tree, "body")
        body.append(content[0])
        return html.tostring(new_tree)

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

    def make_backscrape_iterable(self, kwargs) -> None:
        """Make back scrape iterable

        :param kwargs: the back scraping params
        :return: None
        """
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )
