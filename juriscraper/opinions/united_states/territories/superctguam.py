"""Scraper for Superior Court of Guam
CourtID: superctguam
Court Short Name: Superior Court of Guam
Author: Gianfranco Huaman
History:
  2026-06-24: Created by Gianfranco Huaman
"""

import re
from datetime import date
from urllib.parse import urljoin

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.opinions.united_states.territories import guam


class Site(guam.Site):
    base_url = "https://guamcourts.gov/courts-council/superior-court/decisions-and-orders"
    legacy_url = "https://guamcourts.gov/legacydata/superior-court-decisions"
    legacy_get_items_type = "SUPDO"

    first_opinion_date = date(2009, 1, 1)
    # Normalize mojibake whitespace before parsing
    mojibake_re = re.compile(r"[\xa0\xc2]+")

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.status = "Unknown"

    @override
    def _process_html(self) -> None:
        """Process the current-year decisions and orders page

        Each entry is a ``<p>`` with structured spans and a PDF anchor, e.g.::

            <span class="juryNote">5/29/2026</span>
            <span class="CaseNumber">CF0411-17</span>
            <a href="...pdf">People v. Omagap</a>
            D&O Re Def.'s Mot. ..., 05-28-2026

        The docket is taken as-is from ``span.CaseNumber``. Seen formats:

            CF0411-17
            cv0748-18
            CF0011-21 & CF0586-20
            CF0293-07, CF227-06, CF226-06
            SD0705-03 SD0835-03
            1C0068197
            CF-399-17

        :return: None
        """
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        paragraphs: list[HtmlElement] = self.html.xpath(
            '//div[contains(@class, "field--name-body")]'
            '//p[.//a[contains(@href, ".pdf")]]'
        )
        for paragraph in paragraphs:
            anchor: HtmlElement = paragraph.xpath(
                './/a[contains(@href, ".pdf")]'
            )[0]
            name = anchor.text_content().strip(" ,\r\n")
            url = urljoin(
                (self.url if self.url is not None else ""), anchor.get("href")
            )

            docket_spans: list[HtmlElement] = paragraph.xpath(
                './/span[contains(@class, "CaseNumber")]'
            )
            docket = (
                docket_spans[0].text_content() if bool(docket_spans) else ""
            )
            docket = self.mojibake_re.sub(" ", docket).strip()

            posted_spans: list[HtmlElement] = paragraph.xpath(
                './/span[contains(@class, "juryNote")]'
            )
            posted_date = (
                posted_spans[0].text_content().strip()
                if bool(posted_spans)
                else ""
            )

            description_parts = []
            for sibling in anchor.itersiblings():
                if sibling.tag == "br" and bool(sibling.tail):
                    description_parts.append(sibling.tail.strip())
                elif sibling.tag != "br":
                    description_parts.append(sibling.text_content().strip())
            description = self.mojibake_re.sub(
                " ", " ".join(description_parts)
            ).strip(" .,\r\n")

            row_date = (
                find_date_value
                if bool(find_date_value := self.find_date(description))
                else self.find_date(posted_date)
            )
            if not bool(row_date):
                logger.warning("superctguam: no date found for '%s'", name)

            self.cases.append(
                {
                    "url": url,
                    "name": name,
                    "docket": docket,
                    "date": (
                        row_date if bool(row_date) else f"{self._year}/07/13"
                    ),
                    "date_filed_is_approximate": row_date is None,
                }
            )

    @override
    def _process_legacy_html(self) -> None:
        """Process the legacy ``get_items`` API HTML, used for backscraping

        Legacy rows use a different layout than the current-year page: the
        docket sits in a bold ``<div>``, not ``span.CaseNumber``::

            <div>Posted: 12/23/2024</div>
            <div style="font-weight: bold;">CF0579-12</div>
            <h4><a href="...pdf">People v. Camacho</a></h4>
            <p>D&O Re ..., 12-16-2024</p>

        The docket is taken as-is from that bold div. The same formats listed
        in ``_process_html`` appear on legacy rows, including multi-docket
        values such as ``CF0011-21 & CF0586-20``.

        :return: None
        """
        middle_of_the_year = f"{self._year}/07/13"

        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        items: list[HtmlElement] = self.html.xpath(
            '//div[contains(@class, "item_for_list")]'
        )
        for item in items:
            anchors: list[HtmlElement] = item.xpath(".//h4/a")
            if not bool(anchors):
                logger.warning(
                    "superctguam: legacy row without PDF link, skipping"
                )
                continue

            anchor = anchors[0]
            name = anchor.text_content().strip()
            url = anchor.attrib["href"]

            docket_divs: list[HtmlElement] = item.xpath(
                './/div[contains(@style, "font-weight: bold")]'
            )
            docket = docket_divs[0].text_content() if bool(docket_divs) else ""
            docket = self.mojibake_re.sub(" ", docket).strip()

            description: str = " ".join(item.xpath(".//p//text()")).strip()
            description = self.mojibake_re.sub(" ", description)
            row_date = self.find_date(description)

            self.cases.append(
                {
                    "url": url,
                    "name": name,
                    "docket": docket,
                    "date": (
                        row_date if bool(row_date) else middle_of_the_year
                    ),
                    "date_filed_is_approximate": row_date is None,
                }
            )
