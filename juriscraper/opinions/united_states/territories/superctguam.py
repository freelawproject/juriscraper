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

from juriscraper.AbstractSite import logger
from juriscraper.opinions.united_states.territories import guam


# Most of this site is the same as guam.py
class Site(guam.Site):
    base_url = "https://guamcourts.gov/courts-council/superior-court/decisions-and-orders"
    legacy_url = "https://guamcourts.gov/legacydata/superior-court-decisions"
    legacy_get_items_type = "SUPDO"

    first_opinion_date = date(2009, 1, 1)

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
        paragraphs = self.html.xpath(
            '//div[contains(@class, "field--name-body")]'
            '//p[.//a[contains(@href, ".pdf")]]'
        )
        for paragraph in paragraphs:
            anchor = paragraph.xpath('.//a[contains(@href, ".pdf")]')[0]
            name = anchor.text_content().strip(" ,\r\n")
            url = urljoin(self.url, anchor.get("href"))

            docket_spans = paragraph.xpath(
                './/span[contains(@class, "CaseNumber")]'
            )
            docket = docket_spans[0].text_content() if docket_spans else ""
            # \xc2\xa0 is mojibake, breaks the date regex, same as in guam.py
            docket = re.sub(r"[\xa0\xc2]+", " ", docket).strip()

            posted_spans = paragraph.xpath(
                './/span[contains(@class, "juryNote")]'
            )
            posted_date = (
                posted_spans[0].text_content().strip() if posted_spans else ""
            )

            description_parts = []
            for sibling in anchor.itersiblings():
                if sibling.tag == "br" and sibling.tail:
                    description_parts.append(sibling.tail.strip())
                elif sibling.tag != "br":
                    description_parts.append(sibling.text_content().strip())
            description = re.sub(
                r"[\xa0\xc2]+", " ", " ".join(description_parts)
            ).strip(" .,\r\n")

            row_date = self.find_date(description) or self.find_date(
                posted_date
            )
            if not row_date:
                logger.warning("superctguam: no date found for '%s'", name)

            self.cases.append(
                {
                    "url": url,
                    "name": name,
                    "docket": docket,
                    "date": row_date or f"{self._year}/07/13",
                    "date_filed_is_approximate": row_date is None,
                }
            )

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

        for item in self.html.xpath(
            '//div[contains(@class, "item_for_list")]'
        ):
            anchors = item.xpath(".//h4/a")
            if not anchors:
                continue

            anchor = anchors[0]
            name = anchor.text_content().strip()
            url = anchor.get("href")

            docket_divs = item.xpath(
                './/div[contains(@style, "font-weight: bold")]'
            )
            docket = docket_divs[0].text_content() if docket_divs else ""
            docket = re.sub(r"[\xa0\xc2]+", " ", docket).strip()

            description = re.sub(
                r"[\xa0\xc2]+",
                " ",
                " ".join(item.xpath(".//p//text()")).strip(),
            )
            row_date = self.find_date(description)

            self.cases.append(
                {
                    "url": url,
                    "name": name,
                    "docket": docket,
                    "date": row_date or middle_of_the_year,
                    "date_filed_is_approximate": row_date is None,
                }
            )
