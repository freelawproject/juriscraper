"""Scraper for the Federal Labor Relations Authority
CourtID: flra
Court Short Name: FLRA
Type: Published
History:
    2026-11-01: Created. See #1787

The Authority decisions listing is a Drupal view. Each decision takes two
table rows: the first has citation, issuance number, issuance date, case
number and (for arbitration cases) arbitrator; the second has the document
links and the parties. Recent decisions have a PDF; older ones (back to
1 FLRA, 1979) only have an HTML version.

The view accepts an issuance date range filter, which the backscraper uses.
"""

import re
from datetime import date, datetime
from urllib.parse import urlencode, urljoin

from lxml import html
from typing_extensions import override

from juriscraper.AbstractSite import logger
from juriscraper.lib.exceptions import InvalidDocumentError
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.flra.gov/decisions/authority-decisions"
    first_opinion_date = datetime(1979, 1, 23)
    days_interval = 90

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = f"{self.base_url}?{urlencode({'order': 'issuance_date', 'sort': 'desc'})}"
        self.make_backscrape_iterable(kwargs)

    @override
    def _process_html(self) -> None:
        for first_row in self.html.xpath(
            "//tbody/tr[contains(@class, 'first')]"
        ):
            second_rows = first_row.xpath("following-sibling::tr[1]")
            if not second_rows:
                logger.warning(
                    "flra: no links row after %s", first_row.text_content()
                )
                continue
            links_row = second_rows[0]

            citation = self._cell(first_row, "ad-citation-number")
            date_str = self._cell(first_row, "issuance-date")
            docket = self._cell(first_row, "case-number")

            # Prefer the PDF, fall back to the HTML version
            pdf = links_row.xpath(".//a[normalize-space(.)='PDF']/@href")
            html_link = links_row.xpath(
                ".//a[contains(@class, 'html-link')]/@href"
            )
            if not (pdf or html_link):
                logger.warning("flra: no document link for %s", citation)
                continue
            url = urljoin(self.base_url, (pdf or html_link)[0])

            name_cells = links_row.xpath("./td[@colspan]")
            name = (
                " ".join(name_cells[0].text_content().split())
                if name_cells
                else ""
            )

            self.cases.append(
                {
                    "name": name,
                    "url": url,
                    "date": date_str,
                    "docket": docket,
                    "citation": self._normalize_citation(citation),
                }
            )

    @staticmethod
    def _cell(row, field: str) -> str:
        """Get a cell's text without the mobile-only label div

        :param row: the first row of a decision
        :param field: the views-field class suffix
        :return: the cell's text
        """
        cells = row.xpath(f"./td[contains(@class, 'views-field-{field}')]")
        if not cells:
            return ""
        text = "".join(
            cells[0].xpath(
                "./text() | ./*[not(contains(@class, 'label'))]//text()"
            )
        )
        return " ".join(text.split())

    @staticmethod
    def _normalize_citation(citation: str) -> str:
        """Drop the zero padding on early volumes: '01 FLRA 75' -> '1 FLRA 75'

        :param citation: the citation as displayed
        :return: the normalized citation
        """
        return re.sub(r"^0+(\d)", r"\1", citation)

    @staticmethod
    def cleanup_content(content: bytes) -> bytes | str:
        """Strip site navigation from HTML-only decisions; pass PDFs through

        :param content: the downloaded document
        :return: the PDF bytes, or the decision's <article> HTML
        """
        if content[:5] == b"%PDF-":
            return content
        nodes = html.fromstring(content).xpath("//article")
        if not nodes:
            raise InvalidDocumentError(
                "flra: decision <article> missing from HTML page"
            )
        return html.tostring(nodes[0], encoding="unicode")

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Scrape every page of results for an issuance date range

        :param dates: (start_date, end_date) tuple
        :return: None
        """
        logger.info("Backscraping for range %s %s", *dates)
        params = {
            "issuance_date_op": "between",
            "issuance_date[min]": dates[0].strftime("%Y-%m-%d"),
            "issuance_date[max]": dates[1].strftime("%Y-%m-%d"),
            "order": "issuance_date",
            "sort": "desc",
        }
        page = 0
        while True:
            self.url = f"{self.base_url}?{urlencode({**params, 'page': page})}"
            self.html = await self._download()
            self._process_html()
            if not self.html.xpath("//a[@rel='next']"):
                break
            page += 1
